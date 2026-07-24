import datetime

class CrimeNumberService:
    @staticmethod
    def generate_crime_number(
        category_code: int,
        district_id: int,
        police_station_id: int,
        year: int,
        running_serial: int
    ) -> str:
        """
        Generates the official Karnataka Crime Number based on Datathon rules.
        Format:
        1 digit Case Category Code + 
        4 digit District ID + 
        4 digit Police Station ID (Unit ID) + 
        4 digit Year + 
        5 digit Running Serial Number
        """
        return f"{category_code:01d}{district_id:04d}{police_station_id:04d}{year:04d}{running_serial:05d}"

    @staticmethod
    def parse_crime_number(crime_no: str) -> dict:
        """
        Parses a valid 18-digit Karnataka Crime Number back into its constituent parts.
        """
        if len(crime_no) != 18:
            raise ValueError(f"Invalid Crime Number length: expected 18, got {len(crime_no)}")
        
        return {
            "category_code": int(crime_no[0:1]),
            "district_id": int(crime_no[1:5]),
            "police_station_id": int(crime_no[5:9]),
            "year": int(crime_no[9:13]),
            "running_serial": int(crime_no[13:18])
        }

    @staticmethod
    def generate_case_number(year: int, running_serial: int) -> str:
        """
        Generates the 9-digit Case Number.
        Format: YYYY + 5-digit running serial number (e.g., 202600001).
        """
        return f"{year:04d}{running_serial:05d}"
