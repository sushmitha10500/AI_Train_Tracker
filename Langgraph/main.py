"""
🚆 SIMPLIFIED Indian Railway Route Planner
- Shows only available trains with best routes
- Clear connection details with waiting times
- AI-recommended best option
- User-friendly readable format
- OpenAI version (same logic as working Gemini code)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any, TypedDict
import re
import json
from openai import OpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment")

client = OpenAI(api_key=OPENAI_API_KEY)


BASE = "https://railradar.in/api/v1"

REQUEST_TIMEOUT = 15
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2

# ============================================================
#                  CORE UTILITY FUNCTIONS
# ============================================================

def call_railradar(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Makes API request with retries."""
    url = f"{BASE}{endpoint}"
    params = params or {}

    for attempt in range(RETRY_ATTEMPTS):
        try:
            res = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict) and data.get("success"):
                    return data.get("data", {})
            elif res.status_code == 429:
                time.sleep(RETRY_BACKOFF ** attempt)
                continue
        except Exception as e:
            logger.error(f"API error: {e}")

        if attempt < RETRY_ATTEMPTS - 1:
            time.sleep(RETRY_BACKOFF ** attempt)

    return None


def call_openai_api(user_query: str, system_prompt: str) -> str:
    """
    Calls OpenAI API - matches Gemini's behavior exactly.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        # Extract text content (same as Gemini)
        content = response.choices[0].message.content.strip()
        return content if content else "AI service unavailable."

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "AI service unavailable."


def validate_station_code(code: str) -> bool:
    """Validates station code format - SAME AS GEMINI VERSION."""
    if not code:
        return False
    code = code.strip().upper()
    if not re.match(r'^[A-Z]{2,5}$', code):
        return False
    if len(code) > 5:
        return False
    return True


def validate_station_with_api(station_code: str) -> bool:
    """Validates if a station code exists in the railway system."""
    if not validate_station_code(station_code):
        return False

    # Test the station by checking for trains to a major station
    test_data = call_railradar("/trains/between", params={"from": station_code, "to": "NDLS"})
    if test_data is not None:
        return True

    return False


def mins_to_time(minutes: Optional[int]) -> str:
    """Converts minutes to HH:MM."""
    if minutes is None:
        return "N/A"
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def format_duration(minutes: int) -> str:
    """Formats duration."""
    if minutes < 60:
        return f"{minutes} mins"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"


def get_waiting_recommendation(layover_mins: int) -> Dict:
    """Provides waiting time recommendation."""
    if layover_mins < 30:
        return {
            "status": "⚠ TIGHT",
            "advice": "Very tight connection - risk of missing train",
            "color": "red"
        }
    elif layover_mins < 60:
        return {
            "status": "⏱ MODERATE",
            "advice": "Manageable but rush may be needed",
            "color": "orange"
        }
    elif layover_mins < 180:
        return {
            "status": "✅ COMFORTABLE",
            "advice": "Good buffer time for connections",
            "color": "green"
        }
    else:
        return {
            "status": "🕐 LONG",
            "advice": "Consider exploring nearby areas or refreshments",
            "color": "blue"
        }


# ============================================================
#        FIND NEAREST STATION - AI POWERED WITH VALIDATION
# ============================================================

def find_nearest_station(location: str) -> Optional[Dict]:
    """
    AI-powered station finding with validation and nearest station suggestions.
    """
    logger.info(f"🔍 AI Searching station for: {location}")

    location_clean = location.strip().upper()

    # Check if it's already a valid code
    if len(location_clean) <= 5 and validate_station_code(location_clean):
        logger.info(f"✅ Using provided code: {location_clean}")
        # Validate with API
        if validate_station_with_api(location_clean):
            return {"code": location_clean, "name": location_clean, "confidence": "high"}
        else:
            logger.warning(f"❌ Station code not found in system: {location_clean}")
            # Try to find correct station using AI
            return find_station_with_ai_and_validation(location_clean, is_code=True)

    # Use AI to find station code with enhanced validation
    return find_station_with_ai_and_validation(location_clean, is_code=False)


def find_station_with_ai_and_validation(location: str, is_code: bool = False) -> Optional[Dict]:
    """Find station using AI with API validation and nearest station fallbacks."""

    if is_code:
        system_prompt = """You are an expert on Indian Railway station codes.

A user provided a station code that might be incorrect or misspelled. Find the correct station code and suggest nearest stations.

RULES:
1. If the code is wrong, provide the correct one
2. Suggest 2-3 nearest major stations
3. Include station names and codes
4. Be accurate with railway knowledge

Return ONLY this JSON:
{
  "corrected_code": "SVDK",
  "corrected_name": "SHRI MATA VAISHNO DEVI KATRA",
  "confidence": "high",
  "nearest_stations": [
    {"code": "JAT", "name": "JAMMU TAWI", "distance": "20 km"},
    {"code": "UHP", "name": "JAMMU RAJOURI", "distance": "25 km"}
  ],
  "explanation": "The provided code was incorrect. SVDK is the main station for Vaishno Devi."
}"""
        user_query = f"Correct this possibly wrong station code: {location}"
    else:
        system_prompt = """You are an expert on Indian Railway station codes.

Convert a location/city name to its EXACT official Indian Railway station code and suggest nearest alternatives.

RULES:
1. Return the EXACT 2-5 letter station code used by Indian Railways
2. For pilgrimage sites, find the actual railway station (e.g., Vaishno Devi → SVDK)
3. Suggest 2-3 nearest major stations as alternatives
4. Include distances if known
5. Be accurate - use your railway knowledge

IMPORTANT PILGRIMAGE STATIONS:
- Vaishno Devi → SVDK (Shri Mata Vaishno Devi Katra)
- Tirupati → TPTY (Tirupati Main)
- Varanasi → BSB (Varanasi Junction)
- Puri → PURI (Puri)
- Shirdi → SNSI (Sainagar Shirdi)

Return ONLY this JSON:
{
  "code": "SVDK",
  "name": "SHRI MATA VAISHNO DEVI KATRA",
  "confidence": "high",
  "nearest_stations": [
    {"code": "JAT", "name": "JAMMU TAWI", "distance": "20 km"},
    {"code": "UHP", "name": "JAMMU RAJOURI", "distance": "25 km"}
  ],
  "explanation": "SVDK is the nearest railway station to Vaishno Devi temple in Katra."
}"""
        user_query = f"Find the Indian Railway station code for: {location}"

    try:
        result = call_openai_api(user_query, system_prompt)

        if result and result != "AI service unavailable.":
            result = result.strip()
            # Clean markdown if present
            result = re.sub(r'json\s*', '', result)
            result = re.sub(r'\s*', '', result)

            start_idx = result.find('{')
            end_idx = result.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = result[start_idx:end_idx+1]
                parsed = json.loads(json_str)

                # Get the primary station code
                code = parsed.get("corrected_code") or parsed.get("code", "")
                code = code.upper().strip()
                name = parsed.get("corrected_name") or parsed.get("name", "").strip()
                confidence = parsed.get("confidence", "medium")
                nearest_stations = parsed.get("nearest_stations", [])
                explanation = parsed.get("explanation", "")

                if code and len(code) <= 5 and validate_station_code(code):
                    # Validate with API
                    if validate_station_with_api(code):
                        logger.info(f"✅ AI found and validated: {name} ({code})")
                        return {
                            "code": code,
                            "name": name,
                            "confidence": confidence,
                            "nearest_stations": nearest_stations,
                            "explanation": explanation
                        }
                    else:
                        logger.warning(f"❌ AI suggestion failed validation: {code}")
                        # Try nearest stations as fallback
                        return try_nearest_stations_fallback(nearest_stations, location, explanation)

    except Exception as e:
        logger.error(f"AI error: {e}", exc_info=True)

    logger.error(f"❌ Could not find valid station code for: {location}")
    return None


def try_nearest_stations_fallback(nearest_stations: List[Dict], original_location: str, explanation: str) -> Optional[Dict]:
    """Try nearest stations as fallback when primary station fails validation."""
    if not nearest_stations:
        return None

    logger.info(f"🔄 Trying {len(nearest_stations)} nearest stations as fallback")

    for station in nearest_stations:
        station_code = station.get("code", "").upper().strip()
        station_name = station.get("name", "").strip()
        distance = station.get("distance", "unknown")

        if station_code and validate_station_code(station_code) and validate_station_with_api(station_code):
            logger.info(f"✅ Found valid nearest station: {station_name} ({station_code}) - {distance} away")
            return {
                "code": station_code,
                "name": station_name,
                "confidence": "medium",
                "nearest_stations": [],
                "explanation": f"{explanation} Using nearest station {station_name} ({station_code}) which is {distance} from original location.",
                "is_fallback": True
            }

    return None


# ============================================================
#   FIND ROUTES - ENHANCED WITH AI-POWERED ALTERNATIVES
# ============================================================

def find_all_routes_with_alternatives(from_code: str, to_code: str, from_info: Dict, to_info: Dict) -> List[Dict]:
    """Finds routes with AI-powered alternative station fallbacks."""
    logger.info(f"🔍 Finding routes: {from_code} → {to_code} (with AI alternatives)")

    # Try direct route first
    routes = find_all_routes(from_code, to_code)

    if routes:
        return routes

    # If no routes found, try alternative stations from AI suggestions
    logger.info("🔄 Trying AI-suggested alternative stations...")

    all_alternative_routes = []

    # Try from-station alternatives
    from_alternatives = from_info.get("nearest_stations", [])
    for alt_from in from_alternatives[:3]:
        alt_code = alt_from["code"]
        logger.info(f"🔄 Trying alternative from: {alt_code} ({alt_from.get('distance', 'nearby')})")
        routes = find_all_routes(alt_code, to_code)
        if routes:
            for route in routes:
                route["alternative_note"] = f"From {alt_from['name']} ({alt_code}) instead of {from_info['name']} - {alt_from.get('distance', 'nearby')} away"
            all_alternative_routes.extend(routes)
            break  # Stop at first successful alternative

    # Try to-station alternatives
    to_alternatives = to_info.get("nearest_stations", [])
    for alt_to in to_alternatives[:3]:
        alt_code = alt_to["code"]
        logger.info(f"🔄 Trying alternative to: {alt_code} ({alt_to.get('distance', 'nearby')})")
        routes = find_all_routes(from_code, alt_code)
        if routes:
            for route in routes:
                route["alternative_note"] = f"To {alt_to['name']} ({alt_code}) instead of {to_info['name']} - {alt_to.get('distance', 'nearby')} away"
            all_alternative_routes.extend(routes)
            break  # Stop at first successful alternative

    # Try both alternatives if individual didn't work
    if not all_alternative_routes and from_alternatives and to_alternatives:
        alt_from = from_alternatives[0]
        alt_to = to_alternatives[0]
        logger.info(f"🔄 Trying alternative route: {alt_from['code']} → {alt_to['code']}")
        routes = find_all_routes(alt_from["code"], alt_to["code"])
        if routes:
            for route in routes:
                route["alternative_note"] = f"From {alt_from['name']} to {alt_to['name']} instead of original stations"
            all_alternative_routes.extend(routes)

    return all_alternative_routes[:5]


def find_all_routes(from_code: str, to_code: str) -> List[Dict]:
    """Finds available routes - tries 2-leg first, then 3-leg, then 4-leg."""
    logger.info(f"🔍 Finding routes: {from_code} → {to_code}")

    all_routes = []

    # Check direct trains first
    direct_data = call_railradar("/trains/between", params={"from": from_code, "to": to_code})

    if direct_data and direct_data.get("trains"):
        logger.info(f"✅ Found {len(direct_data['trains'])} direct trains")

        for train in direct_data["trains"][:5]:
            route = {
                "type": "direct",
                "trainNumber": train.get("trainNumber"),
                "trainName": train.get("trainName"),
                "trainType": train.get("type"),
                "departure": mins_to_time(train.get("fromStationSchedule", {}).get("departureMinutes")),
                "arrival": mins_to_time(train.get("toStationSchedule", {}).get("arrivalMinutes")),
                "durationMins": train.get("travelTimeMinutes", 0),
                "distanceKm": train.get("distanceKm", 0),
                "legs": 1,
                "from": from_code,
                "to": to_code
            }
            all_routes.append(route)

    # If no direct trains, try connecting routes
    if len(all_routes) == 0:
        logger.info("🔄 No direct trains found, searching for connections...")
        all_routes = find_connecting_routes(from_code, to_code)

    # Sort by duration (fastest first)
    all_routes.sort(key=lambda x: x.get("durationMins", 999999))

    return all_routes[:5]


def find_connecting_routes(from_code: str, to_code: str) -> List[Dict]:
    """Finds connecting routes - tries 2-leg, then 3-leg, then 4-leg."""
    junctions = [
        "NDLS", "HWH", "MAS", "SBC", "BCT", "CSTM", "PNBE", "LKO", "CNB",
        "ADI", "ST", "BRC", "PUNE", "NGP", "BPL", "JBP", "HYB", "BZA",
        "VSKP", "TVC", "ERS", "CBE", "JP", "AII", "UDR", "JSM", "SVDK", "JAT"
    ]

    junctions = [j for j in junctions if j not in [from_code, to_code]]

    # Try 2-leg routes first
    logger.info("🔍 Trying 2-leg routes...")
    routes = find_2_leg_routes(from_code, to_code, junctions)
    if len(routes) > 0:
        logger.info(f"✅ Found {len(routes)} 2-leg routes")
        return routes

    # If no 2-leg routes, try 3-leg
    logger.info("🔍 No 2-leg routes found, trying 3-leg...")
    routes = find_3_leg_routes(from_code, to_code, junctions)
    if len(routes) > 0:
        logger.info(f"✅ Found {len(routes)} 3-leg routes")
        return routes

    # If no 3-leg routes, try 4-leg
    logger.info("🔍 No 3-leg routes found, trying 4-leg...")
    routes = find_4_leg_routes(from_code, to_code, junctions)
    if len(routes) > 0:
        logger.info(f"✅ Found {len(routes)} 4-leg routes")
        return routes

    logger.warning("❌ No connecting routes found")
    return []


def find_2_leg_routes(from_code: str, to_code: str, junctions: List[str]) -> List[Dict]:
    """Finds 2-leg connecting routes."""
    routes = []

    for junction in junctions[:15]:
        if junction in [from_code, to_code]:
            continue

        leg1_data = call_railradar("/trains/between", params={"from": from_code, "to": junction})
        if not leg1_data or not leg1_data.get("trains"):
            continue

        leg2_data = call_railradar("/trains/between", params={"from": junction, "to": to_code})
        if not leg2_data or not leg2_data.get("trains"):
            continue

        route = build_route_from_legs([
            (from_code, junction, leg1_data["trains"][0]),
            (junction, to_code, leg2_data["trains"][0])
        ])

        if route:
            routes.append(route)
            logger.info(f"✅ Found 2-leg route via {junction}")

        if len(routes) >= 5:
            break

    return routes


def find_3_leg_routes(from_code: str, to_code: str, junctions: List[str]) -> List[Dict]:
    """Finds 3-leg connecting routes."""
    routes = []

    for j1 in junctions[:8]:
        leg1_data = call_railradar("/trains/between", params={"from": from_code, "to": j1})
        if not leg1_data or not leg1_data.get("trains"):
            continue

        for j2 in junctions[:8]:
            if j2 == j1 or j2 in [from_code, to_code]:
                continue

            route = try_3_leg_combination(from_code, to_code, j1, j2)
            if route:
                routes.append(route)
                if len(routes) >= 3:
                    return routes

    return routes


def try_3_leg_combination(from_code: str, to_code: str, j1: str, j2: str) -> Optional[Dict]:
    """Try a specific 3-leg combination."""
    leg1_data = call_railradar("/trains/between", params={"from": from_code, "to": j1})
    if not leg1_data or not leg1_data.get("trains"):
        return None

    leg2_data = call_railradar("/trains/between", params={"from": j1, "to": j2})
    if not leg2_data or not leg2_data.get("trains"):
        return None

    leg3_data = call_railradar("/trains/between", params={"from": j2, "to": to_code})
    if not leg3_data or not leg3_data.get("trains"):
        return None

    route = build_route_from_legs([
        (from_code, j1, leg1_data["trains"][0]),
        (j1, j2, leg2_data["trains"][0]),
        (j2, to_code, leg3_data["trains"][0])
    ])

    if route:
        logger.info(f"✅ Found 3-leg route via {j1}, {j2}")
        return route

    return None


def find_4_leg_routes(from_code: str, to_code: str, junctions: List[str]) -> List[Dict]:
    """Finds 4-leg connecting routes."""
    routes = []

    for j1 in junctions[:6]:
        leg1_data = call_railradar("/trains/between", params={"from": from_code, "to": j1})
        if not leg1_data or not leg1_data.get("trains"):
            continue

        for j2 in junctions[:6]:
            if j2 == j1:
                continue

            leg2_data = call_railradar("/trains/between", params={"from": j1, "to": j2})
            if not leg2_data or not leg2_data.get("trains"):
                continue

            for j3 in junctions[:6]:
                if j3 in [j1, j2]:
                    continue

                route = try_4_leg_combination(from_code, to_code, [j1, j2, j3])
                if route:
                    routes.append(route)
                    return routes

    return routes


def try_4_leg_combination(from_code: str, to_code: str, junctions: List[str]) -> Optional[Dict]:
    """Try a specific 4-leg combination."""
    if len(junctions) != 3:
        return None

    j1, j2, j3 = junctions

    legs_data = []
    current_from = from_code

    for junction in junctions:
        leg_data = call_railradar("/trains/between", params={"from": current_from, "to": junction})
        if not leg_data or not leg_data.get("trains"):
            return None
        legs_data.append((current_from, junction, leg_data["trains"][0]))
        current_from = junction

    # Final leg to destination
    final_leg = call_railradar("/trains/between", params={"from": current_from, "to": to_code})
    if not final_leg or not final_leg.get("trains"):
        return None
    legs_data.append((current_from, to_code, final_leg["trains"][0]))

    route = build_route_from_legs(legs_data)
    if route:
        logger.info(f"✅ Found 4-leg route via {', '.join(junctions)}")
        return route

    return None


def build_route_from_legs(legs: List[tuple]) -> Optional[Dict]:
    """Builds a route object from leg data."""
    segments = []
    total_duration = 0
    total_distance = 0
    layovers = []
    junctions = []
    prev_arrival = None

    for idx, (from_station, to_station, train) in enumerate(legs, 1):
        # Calculate layover
        layover_mins = 0
        if prev_arrival is not None:
            departure = train.get("fromStationSchedule", {}).get("departureMinutes", 0)
            layover_mins = departure - prev_arrival
            if layover_mins < 0:
                layover_mins += 1440

            # More flexible layover constraints
            if layover_mins < 20 or layover_mins > 720:
                return None

            waiting_rec = get_waiting_recommendation(layover_mins)
            layovers.append({
                "station": from_station,
                "waitingTime": format_duration(layover_mins),
                "waitingMins": layover_mins,
                "recommendation": waiting_rec
            })
            total_duration += layover_mins

        segment = {
            "legNumber": idx,
            "trainNumber": train.get("trainNumber"),
            "trainName": train.get("trainName"),
            "trainType": train.get("type"),
            "from": from_station,
            "to": to_station,
            "departure": mins_to_time(train.get("fromStationSchedule", {}).get("departureMinutes")),
            "arrival": mins_to_time(train.get("toStationSchedule", {}).get("arrivalMinutes")),
            "durationMins": train.get("travelTimeMinutes", 0),
            "distanceKm": train.get("distanceKm", 0)
        }

        segments.append(segment)
        total_duration += train.get("travelTimeMinutes", 0)
        total_distance += train.get("distanceKm", 0)
        prev_arrival = train.get("toStationSchedule", {}).get("arrivalMinutes", 0)

        if idx < len(legs):
            junctions.append(to_station)

    return {
        "type": "connecting",
        "legs": len(legs),
        "durationMins": total_duration,
        "distanceKm": total_distance,
        "viaJunctions": junctions,
        "segments": segments,
        "layovers": layovers,
        "from": legs[0][0],
        "to": legs[-1][1]
    }


# ============================================================
#             FORMAT OUTPUT - ENHANCED WITH AI ALTERNATIVES
# ============================================================

def format_routes_for_output(routes: List[Dict], from_info: Dict, to_info: Dict) -> Dict:
    """Formats routes into clean, readable output with AI-powered alternatives."""
    if not routes:
        # Provide intelligent suggestions using AI data
        suggestion = "Try checking nearby major stations or alternative transport options."

        # Use AI-suggested nearest stations for better suggestions
        from_nearest = from_info.get('nearest_stations', [])
        to_nearest = to_info.get('nearest_stations', [])

        if from_nearest or to_nearest:
            suggestion = "Suggested alternative stations: "
            from_stations_str = ", ".join([f"{s['name']} ({s['code']})" for s in from_nearest[:2]])
            to_stations_str = ", ".join([f"{s['name']} ({s['code']})" for s in to_nearest[:2]])

            if from_nearest:
                suggestion += f"From {from_info.get('name')} try: {from_stations_str}. "
            if to_nearest:
                suggestion += f"To {to_info.get('name')} try: {to_stations_str}."

        return {
            "success": False,
            "message": f"❌ No trains found between {from_info.get('name', 'Unknown')} and {to_info.get('name', 'Unknown')}",
            "suggestion": suggestion,
            "debug_info": {
                "from_station": from_info,
                "to_station": to_info,
                "nearest_stations_available": bool(from_nearest or to_nearest)
            }
        }

    response = {
        "success": True,
        "journey": {
            "from": f"{from_info.get('name', 'Unknown')} ({from_info.get('code', 'Unknown')})",
            "to": f"{to_info.get('name', 'Unknown')} ({to_info.get('code', 'Unknown')})",
            "searchDate": datetime.now().strftime("%d %B %Y"),
            "totalOptions": len(routes)
        },
        "aiRecommendation": None,
        "availableTrains": []
    }

    # Add AI explanation if available
    if from_info.get('explanation') or to_info.get('explanation'):
        response["station_info"] = {
            "from_explanation": from_info.get('explanation'),
            "to_explanation": to_info.get('explanation')
        }

    # Format each route
    for idx, route in enumerate(routes, 1):
        if route["type"] == "direct":
            train_info = {
                "option": idx,
                "type": "🚂 DIRECT TRAIN",
                "isRecommended": idx == 1,
                "trainNumber": route["trainNumber"],
                "trainName": route["trainName"],
                "trainType": route["trainType"],
                "departure": {
                    "station": f"{route['from']}",
                    "time": route["departure"]
                },
                "arrival": {
                    "station": f"{route['to']}",
                    "time": route["arrival"]
                },
                "totalJourneyTime": format_duration(route["durationMins"]),
                "totalDistance": f"{route['distanceKm']} km",
                "connections": "No changeovers needed"
            }
        else:
            # Connecting route - FIXED THE BUG HERE
            train_info = {
                "option": idx,
                "type": f"🔄 {route['legs']}-TRAIN CONNECTION",
                "isRecommended": idx == 1 and len([r for r in routes if r["type"] == "direct"]) == 0,
                "totalJourneyTime": format_duration(route["durationMins"]),
                "totalDistance": f"{route['distanceKm']} km",
                "connections": f"{route['legs'] - 1} changeover(s) at {', '.join(route['viaJunctions'])}",
                # FIXED: route['legs'] is int, not len()
                "trains": []
            }

            # Add alternative note if present
            if route.get("alternative_note"):
                train_info["alternative_note"] = route["alternative_note"]

            # Add each train segment
            for seg in route["segments"]:
                train_segment = {
                    "trainNumber": seg["trainNumber"],
                    "trainName": seg["trainName"],
                    "trainType": seg["trainType"],
                    "from": seg["from"],
                    "to": seg["to"],
                    "departure": seg["departure"],
                    "arrival": seg["arrival"],
                    "duration": format_duration(seg["durationMins"]),
                    "distance": f"{seg['distanceKm']} km"
                }
                train_info["trains"].append(train_segment)

            # Add waiting times between trains
            if route["layovers"]:
                train_info["waitingTimes"] = []
                for layover in route["layovers"]:
                    train_info["waitingTimes"].append({
                        "atStation": layover["station"],
                        "waitingTime": layover["waitingTime"],
                        "status": layover["recommendation"]["status"],
                        "advice": layover["recommendation"]["advice"]
                    })

        response["availableTrains"].append(train_info)

    # Generate AI recommendation for best route
    if routes:
        best_route = routes[0]
        if best_route["type"] == "direct":
            response["aiRecommendation"] = {
                "recommendedOption": 1,
                "reason": f"✅ Best Choice: Direct train with fastest journey time of {format_duration(best_route['durationMins'])}. No changeovers required.",
                "highlights": [
                    "No waiting at intermediate stations",
                    "Lower risk of missing connections",
                    "Most convenient option"
                ]
            }
        else:
            total_waiting = sum(l["waitingMins"] for l in best_route["layovers"])
            alternative_note = f" - {best_route.get('alternative_note', '')}" if best_route.get(
                'alternative_note') else ""
            response["aiRecommendation"] = {
                "recommendedOption": 1,
                "reason": f"✅ Best Available: {best_route['legs']}-train connection via {', '.join(best_route['viaJunctions'])}{alternative_note}",
                "totalJourneyTime": format_duration(best_route["durationMins"]),
                "totalWaitingTime": format_duration(total_waiting),
                "highlights": [
                    f"Fastest connecting route available",
                    f"{len(best_route['layovers'])} changeover(s) with comfortable waiting times",
                    "Plan ahead for platform changes"
                ]
            }

    return response


# ============================================================
#                  LANGGRAPH WORKFLOW - ENHANCED
# ============================================================

class AgentState(TypedDict):
    query: str
    intent: str
    extracted_params: Dict[str, Any]
    api_results: Dict[str, Any]
    final_response: str
    errors: List[str]


def extract_intent_and_params(state: AgentState) -> AgentState:
    """Extract intent and parameters."""
    query = state["query"]

    system_prompt = """Extract intent and parameters from railway query.
Return JSON:
{
  "intent": "find_trains",
  "params": {"from": "Guwahati", "to": "Bairabi"}
}"""

    try:
        result = call_openai_api(query, system_prompt)
        result = result.strip().replace("json", "").replace("```", "").strip()
        parsed = json.loads(result)
        state["intent"] = parsed.get("intent", "find_trains")
        state["extracted_params"] = parsed.get("params", {})
    except:
        state["intent"] = "find_trains"
        state["extracted_params"] = {}

    return state


def convert_locations_to_stations(state: AgentState) -> AgentState:
    """Convert locations to station codes with AI-powered validation."""
    params = state["extracted_params"]

    from_loc = params.get("from", "")
    to_loc = params.get("to", "")

    from_station = find_nearest_station(from_loc)
    to_station = find_nearest_station(to_loc)

    if not from_station:
        state["errors"].append(f"Could not find station for: {from_loc}")
    else:
        params["from_code"] = from_station["code"]
        params["from_info"] = from_station

    if not to_station:
        state["errors"].append(f"Could not find station for: {to_loc}")
    else:
        params["to_code"] = to_station["code"]
        params["to_info"] = to_station

    state["extracted_params"] = params
    return state


def find_routes_node(state: AgentState) -> AgentState:
    """Find all possible routes with AI-powered alternatives."""
    params = state["extracted_params"]

    from_code = params.get("from_code")
    to_code = params.get("to_code")
    from_info = params.get("from_info", {})
    to_info = params.get("to_info", {})

    if not from_code or not to_code:
        state["errors"].append("Missing station codes for route search")
        return state

    # Try direct routes first, then AI-powered alternatives
    routes = find_all_routes_with_alternatives(from_code, to_code, from_info, to_info)

    state["api_results"] = {
        "routes": routes,
        "from_info": from_info,
        "to_info": to_info
    }

    return state


def generate_response(state: AgentState) -> AgentState:
    """Generate final response."""
    if state["errors"]:
        state["final_response"] = {
            "success": False,
            "errors": state["errors"],
            "message": "Failed to process your request. Please check station names and try again."
        }
    else:
        formatted = format_routes_for_output(
            state["api_results"].get("routes", []),
            state["api_results"].get("from_info", {}),
            state["api_results"].get("to_info", {})
        )
        state["final_response"] = formatted

    return state


# Build workflow
def create_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("extract_intent", extract_intent_and_params)
    workflow.add_node("convert_stations", convert_locations_to_stations)
    workflow.add_node("find_routes", find_routes_node)
    workflow.add_node("generate_response", generate_response)

    workflow.set_entry_point("extract_intent")
    workflow.add_edge("extract_intent", "convert_stations")
    workflow.add_edge("convert_stations", "find_routes")
    workflow.add_edge("find_routes", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


agent_graph = create_agent_graph()


# ============================================================
#                    FLASK ENDPOINTS
# ============================================================

@app.get("/")
def home():
    return jsonify({
        "service": "🚆 AI-Powered Indian Railway Route Planner",
        "version": "5.0",
        "features": [
            "✅ AI-powered station code detection",
            "🔄 Automatic nearest station suggestions",
            "🤖 Intelligent route alternatives",
            "⏱ Smart validation and fallbacks",
            "📊 Enhanced error handling with suggestions"
        ],
        "endpoints": {
            "GET /health": "Service health check",
            "POST /api/smart_query": "Main query endpoint",
            "GET /api/direct_routes": "Direct route testing"
        }
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "version": "5.0",
        "ai": "OpenAI",
        "timestamp": datetime.now().isoformat()
    })


@app.post("/api/smart_query")
def smart_query():
    """Main query endpoint."""
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 400

    data = request.json
    query = data.get("query", "").strip()

    if not query:
        return jsonify(error="Missing 'query' parameter"), 400

    logger.info(f"📥 Query: {query}")

    initial_state = {
        "query": query,
        "intent": "",
        "extracted_params": {},
        "api_results": {},
        "final_response": "",
        "errors": []
    }

    try:
        result = agent_graph.invoke(initial_state)
        logger.info("✅ Query completed successfully")
        return jsonify(result["final_response"])
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Internal server error. Please try again later."
        }), 500


# Direct route endpoint for testing
@app.get("/api/direct_routes")
def direct_routes():
    """Direct route testing endpoint."""
    from_station = request.args.get("from", "").strip()
    to_station = request.args.get("to", "").strip()

    if not from_station or not to_station:
        return jsonify(error="Missing 'from' or 'to' parameters"), 400

    from_info = find_nearest_station(from_station)
    to_info = find_nearest_station(to_station)

    if not from_info or not to_info:
        return jsonify(error="Invalid station names"), 400

    routes = find_all_routes_with_alternatives(from_info["code"], to_info["code"], from_info, to_info)
    result = format_routes_for_output(routes, from_info, to_info)

    return jsonify(result)


if __name__ == "__main__":
    logger.info("🚆 Starting AI-Powered Railway Planner v5.0 (OpenAI)")
    app.run(host="0.0.0.0", port=5000, debug=True)