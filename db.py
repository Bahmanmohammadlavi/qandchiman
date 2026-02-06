import os
from supabase import create_client, Client
from dotenv import load_dotenv
import jdatetime
from datetime import datetime
from typing import Optional, List, Dict, Any

# Load environment variables
load_dotenv()


class Database:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY")
        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL and Key must be set in environment variables")
        self.client: Client = create_client(self.url, self.key)

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        # Note: You need to create tables manually in Supabase dashboard
        # This is just a helper function
        pass

    def add_test(self, user_id: int, glucose: int, fasting: bool,
                 test_time: str, symptoms: str, notes: Optional[str] = None) -> Optional[Dict]:
        """Add a new glucose test record"""
        try:
            # Get current Jalali date
            now = datetime.now()
            jalali_date = jdatetime.datetime.fromgregorian(datetime=now)
            shamsi_date = jalali_date.strftime("%Y/%m/%d")

            data = {
                "user_id": user_id,
                "glucose": glucose,
                "fasting": fasting,
                "test_time": test_time,
                "symptoms": symptoms,
                "notes": notes,
                "shamsi_date": shamsi_date,
                "created_at": now.isoformat()
            }

            response = self.client.table(
                'glucose_tests').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error adding test: {e}")
            return None

    def get_user_tests(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get all tests for a user"""
        try:
            response = self.client.table('glucose_tests') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting user tests: {e}")
            return []

    def get_weekly_stats(self, user_id: int) -> Dict[str, Any]:
        """Get weekly statistics for a user"""
        try:
            from datetime import datetime, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()

            response = self.client.table('glucose_tests') \
                .select('*') \
                .eq('user_id', user_id) \
                .gte('created_at', week_ago) \
                .execute()

            tests = response.data

            if not tests:
                return {
                    "count": 0,
                    "avg_glucose": 0,
                    "fasting_count": 0,
                    "non_fasting_count": 0,
                    "tests": []
                }

            glucose_values = [t['glucose'] for t in tests]
            fasting_count = len([t for t in tests if t['fasting']])

            return {
                "count": len(tests),
                "avg_glucose": sum(glucose_values) / len(glucose_values),
                "fasting_count": fasting_count,
                "non_fasting_count": len(tests) - fasting_count,
                "tests": tests
            }
        except Exception as e:
            print(f"Error getting weekly stats: {e}")
            return {
                "count": 0,
                "avg_glucose": 0,
                "fasting_count": 0,
                "non_fasting_count": 0,
                "tests": []
            }

    def get_monthly_tests(self, user_id: int, year: int, month: int) -> List[Dict]:
        """Get tests for a specific Jalali month"""
        try:
            # Get start and end of Jalali month
            start_date_jalali = jdatetime.date(year, month, 1)
            if month == 12:
                end_date_jalali = jdatetime.date(year + 1, 1, 1)
            else:
                end_date_jalali = jdatetime.date(year, month + 1, 1)

            start_date_gregorian = start_date_jalali.togregorian()
            end_date_gregorian = end_date_jalali.togregorian()

            response = self.client.table('glucose_tests') \
                .select('*') \
                .eq('user_id', user_id) \
                .gte('created_at', start_date_gregorian.isoformat()) \
                .lt('created_at', end_date_gregorian.isoformat()) \
                .order('created_at', desc=True) \
                .execute()

            return response.data
        except Exception as e:
            print(f"Error getting monthly tests: {e}")
            return []

    def delete_test(self, test_id: int) -> bool:
        """Delete a test by ID"""
        try:
            response = self.client.table(
                'glucose_tests').delete().eq('id', test_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting test: {e}")
            return False

    def get_test_by_id(self, test_id: int) -> Optional[Dict]:
        """Get a test by ID"""
        try:
            response = self.client.table('glucose_tests') \
                .select('*') \
                .eq('id', test_id) \
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting test by ID: {e}")
            return None

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get overall statistics for a user"""
        try:
            response = self.client.table('glucose_tests') \
                .select('*') \
                .eq('user_id', user_id) \
                .execute()

            tests = response.data

            if not tests:
                return {
                    "total_tests": 0,
                    "avg_glucose": 0,
                    "last_test": None,
                    "min_glucose": 0,
                    "max_glucose": 0
                }

            glucose_values = [t['glucose'] for t in tests]

            return {
                "total_tests": len(tests),
                "avg_glucose": sum(glucose_values) / len(glucose_values),
                "min_glucose": min(glucose_values),
                "max_glucose": max(glucose_values),
                "last_test": tests[0] if tests else None
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                "total_tests": 0,
                "avg_glucose": 0,
                "last_test": None,
                "min_glucose": 0,
                "max_glucose": 0
            }


# Create global database instance
db = Database()
