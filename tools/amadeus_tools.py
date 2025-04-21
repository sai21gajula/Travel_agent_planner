# travel_agent/tools/amadeus_tools.py
import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List
# Ensure you have installed the amadeus library: pip install amadeus
from amadeus import Client, ResponseError, Location

# --- Amadeus Client Initialization ---
# Store keys in .env: AMADEUS_CLIENT_ID=YOUR_ID, AMADEUS_CLIENT_SECRET=YOUR_SECRET
amadeus_client = None
try:
    # Initialize client using environment variables
    amadeus_client = Client(
        client_id=os.getenv("AMADEUS_CLIENT_ID"),
        client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
        # hostname='production' # Uncomment for production environment if needed
        log_level='warning' # Set to 'debug' for detailed logs if needed
    )
    print("Amadeus client initialized successfully.")
except Exception as e:
    print(f"Error initializing Amadeus client: {e}. Ensure AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET are set in .env")

# --- Flight Search Tool ---
class AmadeusFlightInput(BaseModel):
    origin_city_code: str = Field(..., description="Origin city or airport IATA code (e.g., 'MAD', 'LHR')")
    destination_city_code: str = Field(..., description="Destination city or airport IATA code (e.g., 'BOS', 'CDG')")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format (optional for one-way)")
    adults: int = Field(1, description="Number of adult passengers (12+ years)")
    max_results: int = Field(5, description="Maximum number of flight offers to return (e.g., 5)")

class AmadeusFlightSearchTool(BaseTool):
    name: str = "amadeus_flight_search"
    description: str = """
    Searches for flight offers using the Amadeus API based on origin/destination IATA codes and dates.
    Returns a list of flight options including price, airlines, and stop information.
    """
    args_schema: Type[BaseModel] = AmadeusFlightInput

    def _run(self, origin_city_code: str, destination_city_code: str, departure_date: str, return_date: Optional[str] = None, adults: int = 1, max_results: int = 5) -> str:
        if not amadeus_client:
            return "Amadeus client not initialized. Check API keys in .env file."

        try:
            search_params = {
                'originLocationCode': origin_city_code,
                'destinationLocationCode': destination_city_code,
                'departureDate': departure_date,
                'adults': adults,
                'max': max_results,
                'currencyCode': 'USD' # Specify currency
            }
            if return_date:
                search_params['returnDate'] = return_date

            # Make the API call using the SDK
            response = amadeus_client.shopping.flight_offers_search.get(**search_params)
            offers = response.data # The SDK parses the JSON response

            if not offers:
                return f"No Amadeus flight offers found for {origin_city_code} to {destination_city_code} on {departure_date}."

            results_str = f"Amadeus Flight Offers for {origin_city_code} to {destination_city_code}:\n\n"
            for i, offer in enumerate(offers[:max_results], 1):
                price = offer.get('price', {}).get('total', 'N/A')
                currency = offer.get('price', {}).get('currency', '')
                itineraries = offer.get('itineraries', [])

                # Determine airline codes involved in the first itinerary's outbound segments
                airline_codes = set()
                if itineraries and itineraries[0].get('segments'):
                    for segment in itineraries[0]['segments']:
                        airline_codes.add(segment.get('carrierCode', '??'))
                airlines = ', '.join(sorted(list(airline_codes))) if airline_codes else 'N/A'

                # Count stops for the first itinerary's outbound leg
                num_stops_outbound = len(itineraries[0]['segments']) - 1 if (itineraries and itineraries[0].get('segments')) else 'N/A'

                results_str += f"{i}. Price: {price} {currency}, Airlines: {airlines}, Stops (Outbound): {num_stops_outbound}\n"
                # Further details like duration or specific segment info can be parsed from 'itineraries' if needed

            return results_str

        except ResponseError as error:
            # Log the detailed error for debugging
            print(f"Amadeus API Response Error (Flight Search): Status={error.response.status_code}, Code={error.code}, Details={error.description}")
            return f"Amadeus API Error (Flight Search): {error.code} - Check input parameters and API key validity."
        except Exception as e:
            print(f"Unexpected Error processing Amadeus flight search: {str(e)}")
            return f"Unexpected error during Amadeus flight search: {str(e)}"

# --- Hotel Search Tool ---
class AmadeusHotelInput(BaseModel):
    city_code: str = Field(..., description="IATA city code (e.g., 'PAR', 'LON') for the hotel search")
    check_in_date: Optional[str] = Field(None, description="Check-in date (YYYY-MM-DD). Optional, but helps refine offers.")
    check_out_date: Optional[str] = Field(None, description="Check-out date (YYYY-MM-DD). Optional.")
    adults: int = Field(1, description="Number of adults")
    max_results: int = Field(5, description="Maximum number of hotels to return")

class AmadeusHotelSearchTool(BaseTool):
    name: str = "amadeus_hotel_search"
    description: str = """
    Searches for hotel availability and offers in a specific city using the Amadeus API.
    Requires the IATA city code (e.g., 'PAR'). Dates and guest count are optional but recommended.
    Returns a list of hotels with names, address, rating and approximate price if available.
    """
    args_schema: Type[BaseModel] = AmadeusHotelInput

    def _run(self, city_code: str, check_in_date: Optional[str] = None, check_out_date: Optional[str] = None, adults: int = 1, max_results: int = 5) -> str:
        if not amadeus_client:
            return "Amadeus client not initialized. Check API keys in .env file."

        try:
            search_params = {
                'cityCode': city_code,
                'adults': adults,
                'radius': 20, # Search within a 20km radius (adjust as needed)
                'radiusUnit': 'KM',
                'paymentPolicy': 'NONE', # Simplest policy for broad search
                'includeClosed': False,
                'bestRateOnly': True,
                'view': 'LIGHT', # LIGHT view is often sufficient for listing
                'sort': 'DISTANCE' # Other options: 'PRICE', 'RATING'
            }
            if check_in_date:
                search_params['checkInDate'] = check_in_date
            if check_out_date:
                search_params['checkOutDate'] = check_out_date

            # Use the hotel_offers endpoint for searching by cityCode
            response = amadeus_client.shopping.hotel_offers.get(**search_params)
            hotels_data = response.data

            if not hotels_data:
                return f"No Amadeus hotel offers found for city code {city_code}."

            results_str = f"Amadeus Hotel Options in {city_code}:\n\n"
            count = 0
            for hotel_entry in hotels_data:
                if count >= max_results:
                    break

                hotel_info = hotel_entry.get('hotel', {})
                hotel_name = hotel_info.get('name', 'N/A')
                hotel_id = hotel_info.get('hotelId', 'N/A') # Useful for subsequent detailed searches
                address_info = hotel_info.get('address', {})
                address_lines = address_info.get('lines', [])
                address = address_lines[0] if address_lines else 'N/A'
                city = address_info.get('cityName', 'N/A')
                country = address_info.get('countryCode', 'N/A')
                rating = hotel_info.get('rating', 'N/A')

                # Attempt to get price from the first available offer in the response
                offer_price = 'N/A'
                currency = ''
                if hotel_entry.get('offers'):
                    offer = hotel_entry['offers'][0]
                    price_info = offer.get('price', {})
                    offer_price = price_info.get('total', price_info.get('base', 'N/A')) # Try total, fallback to base
                    currency = price_info.get('currency', '')

                results_str += f"{count+1}. Name: {hotel_name} (ID: {hotel_id})\n"
                results_str += f"   Address: {address}, {city}, {country}\n"
                results_str += f"   Rating: {rating}-star\n"
                results_str += f"   Price (approx): {offer_price} {currency}\n\n"
                count += 1

            if count == 0: # If loop didn't run but hotels_data was not empty
                 return f"Found hotel data for {city_code}, but could not parse details or offers."

            return results_str

        except ResponseError as error:
            print(f"Amadeus API Response Error (Hotel Search): Status={error.response.status_code}, Code={error.code}, Details={error.description}")
            # Handle common errors like invalid city code
            if error.response and error.response.status_code == 400:
                 return f"Amadeus API Error (Hotel Search): Bad request - Check if '{city_code}' is a valid IATA city code and other parameters are correct."
            if error.response and error.response.status_code == 404:
                 return f"Amadeus API Error (Hotel Search): Could not find hotel information for city code: {city_code}."
            return f"Amadeus API Error (Hotel Search): {error.code} - Check input parameters and API key validity."
        except Exception as e:
            print(f"Unexpected Error processing Amadeus hotel search: {str(e)}")
            return f"Unexpected error during Amadeus hotel search: {str(e)}"