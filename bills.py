import mysql.connector
from datetime import datetime, timedelta
import calendar
# import smtplib




class Bills:
    def __init__(self, num_reps=50, db_connection=None):
        self.num_reps = num_reps
        self.today = ""
        self.next_pay_day = None
        self.user_id = None
        self.db = db_connection
        self.cursor = self.db.cursor(dictionary=True) if db_connection else None
        
    def _ensure_string_date(self, date_value):
        """Convert date object to string if needed"""
        if date_value is None:
            return None
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d")
        elif hasattr(date_value, 'strftime'):  # datetime.date object
            return date_value.strftime("%Y-%m-%d")
        elif isinstance(date_value, str):
            # Handle empty strings and invalid dates
            if date_value.strip() == "" or date_value == "0000-00-00":
                return None
            return date_value.strip()
        else:
            return str(date_value) if date_value else None
        
    def set_pay_period(self, next_pay_day="", today=""):
        """Set the pay period based on current date"""
        if not today:
            today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        start_date = today
        start_day = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").day)
        
        if start_day < 15:
            # Next pay day is the 14th of current month
            current_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            next_pay_day = current_date.replace(day=14).strftime("%Y-%m-%d")
        else:
            # Next pay day is the last day of current month
            current_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            next_pay_day = current_date.replace(day=last_day).strftime("%Y-%m-%d")
        
        self.today = today
        self.next_pay_day = next_pay_day
        
    def delete_old_dates(self):
        """Clean up old bill dates and expired 'Once' bills"""
        # Truncate bill dates table
        query = "TRUNCATE vnd_bill_dates"
        self.cursor.execute(query)
        
        # Delete expired 'Once' bills
        sql = """DELETE FROM vnd_bills 
                 WHERE vnd_frequency = 'Once' 
                 AND DATE_SUB(NOW(), INTERVAL 2 DAY) > DATE(vnd_frequency_value)"""
        self.cursor.execute(sql)
        self.db.commit()
        
    def load_bills_by_user_id(self, user_id):
        """Load all bills for a specific user"""
        query = """SELECT * FROM vnd_bills 
                   WHERE vnd_user_id = %s 
                   ORDER BY vnd_frequency, vnd_frequency_type"""
        
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()
        
    def load_bill_dates_by_user_id(self, user_id):
        """Load bill dates for a specific user within the pay period"""
        query = """SELECT * FROM vnd_bill_dates 
                   WHERE vnd_user_id = %s
                   AND vnd_date BETWEEN %s AND %s
                   ORDER BY vnd_date, vnd_bill_desc"""
        
        self.cursor.execute(query, (user_id, self.today, self.next_pay_day))
        return self.cursor.fetchall()
        
    def check_date_exists(self, bill_desc, date, user_id):
        """Check if a bill date already exists"""
        query = """SELECT vnd_id FROM vnd_bill_dates 
                   WHERE vnd_bill_desc = %s 
                   AND vnd_date = %s 
                   AND vnd_user_id = %s 
                   LIMIT 1"""
        
        self.cursor.execute(query, (bill_desc, date, user_id))
        return len(self.cursor.fetchall()) > 0
        
    def insert_bill_date(self, bill_desc, user_id, amount, date, is_future=0, 
                        is_heavy=0, vnd_frequency="", vnd_frequency_type=""):
        """Insert a new bill date"""
        query = """INSERT INTO vnd_bill_dates 
                   (vnd_bill_desc, vnd_user_id, vnd_amount, vnd_date, vnd_is_future, 
                    is_heavy, vnd_frequency, vnd_frequency_type) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        
        self.cursor.execute(query, (bill_desc, user_id, amount, date, is_future, 
                                   is_heavy, vnd_frequency, vnd_frequency_type))
        
    def load_once(self, freq_value, bill_desc, amount, freq_type, is_future=0, 
                  is_heavy=0, vnd_frequency="", vnd_frequency_type=""):
        """Load a one-time bill"""
        freq_value_str = self._ensure_string_date(freq_value)
        if not self.check_date_exists(bill_desc, freq_value_str, self.user_id):
            self.insert_bill_date(bill_desc, self.user_id, amount, freq_value_str, 
                                 is_future, is_heavy, vnd_frequency, vnd_frequency_type)
            
    def load_once_per_month(self, freq_value, bill_desc, amount, freq_type="Day of Month", 
                           is_future=0, is_heavy=0, vnd_frequency="", vnd_frequency_type="",
                           end_date=None, start_date=None):
        """Load monthly recurring bills"""
        if freq_type == "Day of Month":
            # Validate and convert freq_value to int
            try:
                if not freq_value or str(freq_value).strip() == "":
                    print(f"Warning: Empty freq_value for bill '{bill_desc}', skipping")
                    return
                freq_value = int(freq_value)
                if freq_value < 1 or freq_value > 31:
                    print(f"Warning: Invalid day of month '{freq_value}' for bill '{bill_desc}', skipping")
                    return
            except (ValueError, TypeError) as e:
                print(f"Warning: Cannot convert freq_value '{freq_value}' to integer for bill '{bill_desc}': {e}")
                return
                
            today_date = datetime.strptime(self.today, "%Y-%m-%d %H:%M:%S")
            month = today_date.month
            year = today_date.year
            
            for i in range(self.num_reps):
                # Handle February with day > 28
                if month == 2 and freq_value > 28:
                    freq_value = 28
                    
                if freq_value < 32:
                    try:
                        bill_date = datetime(year, month, freq_value)
                        date_str = bill_date.strftime("%Y-%m-%d")
                        
                        # Check future validation
                        passes_future_validation = True
                        if end_date and end_date != "0000-00-00":
                            end_date_str = self._ensure_string_date(end_date)
                            if end_date_str and bill_date > datetime.strptime(end_date_str, "%Y-%m-%d"):
                                passes_future_validation = False
                                
                        # Check past validation  
                        passes_prev_validation = True
                        if start_date and start_date != "0000-00-00":
                            start_date_str = self._ensure_string_date(start_date)
                            if start_date_str and bill_date < datetime.strptime(start_date_str, "%Y-%m-%d"):
                                passes_prev_validation = False
                                
                        if passes_future_validation and passes_prev_validation:
                            if not self.check_date_exists(bill_desc, date_str, self.user_id):
                                self.insert_bill_date(bill_desc, self.user_id, amount, date_str,
                                                     is_future, is_heavy, vnd_frequency, vnd_frequency_type)
                    except ValueError:
                        # Invalid date (like Feb 30), skip
                        pass
                        
                # Move to next month
                if month < 12:
                    month += 1
                else:
                    year += 1
                    month = 1
                    
    def load_every_x_months(self, freq_value, bill_desc, amount, freq_type="Starting From", 
                           num_months=1, is_future=0, is_heavy=0, vnd_frequency="", 
                           vnd_frequency_type=""):
        """Load bills that occur every X months"""
        if freq_type == "Starting From":
            num_days = num_months * 30
            freq_value_str = self._ensure_string_date(freq_value)
            if not freq_value_str:
                print(f"Warning: Invalid freq_value for Every X Months: {freq_value}")
                return
            try:
                start_date = datetime.strptime(freq_value_str, "%Y-%m-%d")
            except ValueError as e:
                print(f"Error parsing date '{freq_value_str}': {e}")
                return
            each_date = start_date
            
            if num_months == 0:
                num_months = 1
                
            for i in range(self.num_reps):
                use_date = each_date + timedelta(days=num_days)
                date_str = use_date.strftime("%Y-%m-%d")
                
                if not self.check_date_exists(bill_desc, date_str, self.user_id):
                    self.insert_bill_date(bill_desc, self.user_id, amount, date_str,
                                         is_future, is_heavy, vnd_frequency, vnd_frequency_type)
                
                each_date = use_date
                
    def load_once_per_week(self, freq_value, bill_desc, amount, freq_type="Day of Week", 
                          is_future=0, is_heavy=0, vnd_frequency="", vnd_frequency_type=""):
        """Load weekly recurring bills"""
        if freq_type == "Day of Week":
            # Validate and convert freq_value to int
            try:
                if not freq_value or str(freq_value).strip() == "":
                    print(f"Warning: Empty freq_value for bill '{bill_desc}', skipping")
                    return
                target_day = int(freq_value)
                if target_day < 0 or target_day > 6:
                    print(f"Warning: Invalid day of week '{target_day}' for bill '{bill_desc}', skipping")
                    return
            except (ValueError, TypeError) as e:
                print(f"Warning: Cannot convert freq_value '{freq_value}' to integer for bill '{bill_desc}': {e}")
                return
                
            today_date = datetime.strptime(self.today, "%Y-%m-%d %H:%M:%S")
            current_day = today_date.weekday()  # Monday = 0, Sunday = 6
            
            # Convert PHP weekday (Sunday=0) to Python weekday (Monday=0)
            if target_day == 0:  # Sunday in PHP
                target_day = 6  # Sunday in Python
            else:
                target_day -= 1  # Adjust for Monday=0 in Python
                
            weekday_diff = target_day - current_day
            if weekday_diff <= 0:
                weekday_diff += 7
                
            start_date = today_date + timedelta(days=weekday_diff)
            each_date = start_date
            
            for i in range(self.num_reps):
                use_date = each_date + timedelta(days=7)
                date_str = use_date.strftime("%Y-%m-%d")
                
                if not self.check_date_exists(bill_desc, date_str, self.user_id):
                    self.insert_bill_date(bill_desc, self.user_id, amount, date_str,
                                         is_future, is_heavy, vnd_frequency, vnd_frequency_type)
                
                each_date = use_date
                
    def load_every_x_weeks(self, freq_value, bill_desc, amount, freq_type="Starting From", 
                          num_weeks=2, is_future=0, is_heavy=0, vnd_frequency="", 
                          vnd_frequency_type=""):
        """Load bills that occur every X weeks"""
        if freq_type == "Starting From":
            num_days = num_weeks * 7
            freq_value_str = self._ensure_string_date(freq_value)
            if not freq_value_str:
                print(f"Warning: Invalid freq_value for Every X Weeks: {freq_value}")
                return
            try:
                start_date = datetime.strptime(freq_value_str, "%Y-%m-%d")
            except ValueError as e:
                print(f"Error parsing date '{freq_value_str}': {e}")
                return
            each_date = start_date
            
            if num_weeks == 0:
                num_weeks = 1
                
            for i in range(self.num_reps):
                use_date = each_date + timedelta(days=num_days)
                date_str = use_date.strftime("%Y-%m-%d")
                
                if not self.check_date_exists(bill_desc, date_str, self.user_id):
                    self.insert_bill_date(bill_desc, self.user_id, amount, date_str,
                                         is_future, is_heavy, vnd_frequency, vnd_frequency_type)
                
                each_date = use_date
                
    def generate_bill_dates_by_user_id(self, user_id):
        """Generate all bill dates for a user based on their bill frequencies"""
        self.user_id = user_id
        bills = self.load_bills_by_user_id(user_id)
        
        for bill in bills:
            try:
                frequency = bill['vnd_frequency']
                print(f"Processing bill: {bill.get('vnd_bill', 'Unknown')} with frequency: {frequency}")
                
                if frequency == "Once":
                    print(f"  -> Processing as 'Once' with value: {bill['vnd_frequency_value']}")
                    self.load_once(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type']
                    )
                elif frequency == "Once Per Month":
                    print(f"  -> Processing as 'Once Per Month' with value: {bill['vnd_frequency_value']}, type: {bill['vnd_frequency_type']}")
                    self.load_once_per_month(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type'],
                        bill.get('end_date'), bill.get('start_date')
                    )
                elif frequency == "Every 3 Months":
                    print(f"  -> Processing as 'Every 3 Months' with value: {bill['vnd_frequency_value']}, type: {bill['vnd_frequency_type']}")
                    self.load_every_x_months(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], 3, bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type']
                    )
                elif frequency == "Every 1 Month":
                    print(f"  -> Processing as 'Every 1 Month' with value: {bill['vnd_frequency_value']}, type: {bill['vnd_frequency_type']}")
                    self.load_every_x_months(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], 1, bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type']
                    )
                elif frequency == "Once Per Week":
                    print(f"  -> Processing as 'Once Per Week' with value: {bill['vnd_frequency_value']}, type: {bill['vnd_frequency_type']}")
                    self.load_once_per_week(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type']
                    )
                elif frequency == "Every 2 Weeks":
                    print(f"  -> Processing as 'Every 2 Weeks' with value: {bill['vnd_frequency_value']}, type: {bill['vnd_frequency_type']}")
                    self.load_every_x_weeks(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], 2, bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type']
                    )
                elif frequency == "Every 1 Week":
                    print(f"  -> Processing as 'Every 1 Week' with value: {bill['vnd_frequency_value']}, type: {bill['vnd_frequency_type']}")
                    self.load_every_x_weeks(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], 1, bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type']
                    )
                elif frequency == "Every 4 Weeks":
                    print(f"  -> Processing as 'Every 4 Weeks' with value: {bill['vnd_frequency_value']}, type: {bill['vnd_frequency_type']}")
                    self.load_every_x_weeks(
                        bill['vnd_frequency_value'], bill['vnd_bill'], bill['amount'],
                        bill['vnd_frequency_type'], 4, bill.get('is_future', 0), 
                        bill.get('is_heavy', 0), bill['vnd_frequency'], bill['vnd_frequency_type']
                    )
                else:
                    print(f"  -> Unknown frequency type: {frequency}")
            except Exception as e:
                print(f"Error processing bill {bill.get('vnd_bill', 'Unknown')} (freq: {frequency}): {str(e)}")
                # Continue processing other bills instead of stopping
                continue
        
        self.db.commit()
        
    # def send_future_charges(self):
    #     """Send email notification for upcoming future charges"""
    #     date_from = datetime.now().strftime("%Y-%m-%d")
    #     current_day = datetime.now().day
        
    #     if current_day < 15:
    #         # End of current month
    #         today = datetime.now()
    #         last_day = calendar.monthrange(today.year, today.month)[1]
    #         date_to = today.replace(day=last_day).strftime("%Y-%m-%d")
    #     else:
    #         # 15th of next month
    #         today = datetime.now()
    #         if today.month == 12:
    #             next_month = today.replace(year=today.year + 1, month=1, day=15)
    #         else:
    #             next_month = today.replace(month=today.month + 1, day=15)
    #         date_to = next_month.strftime("%Y-%m-%d 23:59:59")
        
    #     query = """SELECT bd.vnd_bill_desc, bd.vnd_date, bd.vnd_amount
    #                FROM vnd_bill_dates bd
    #                WHERE vnd_is_future = 1
    #                AND vnd_date BETWEEN %s AND %s"""
        
    #     self.cursor.execute(query, (date_from, date_to))
    #     results = self.cursor.fetchall()
        
    #     if results:
    #         email_content = "Hello, you have the following Appointments coming up in this paycheck, or the following:<br><br>"
            
    #         for item in results:
    #             bill_date = datetime.strptime(item['vnd_date'], "%Y-%m-%d")
    #             formatted_date = bill_date.strftime("%m/%d/%Y")
    #             amount = round(float(item['vnd_amount']), 2)
    #             email_content += f"- {item['vnd_bill_desc']}, on {formatted_date}, for the amount: ${amount}<br>"
            
    #         # Send email (you'll need to configure SMTP settings)
    #         self.send_email("ahawley@claimatic.com", "Appointments this Week", email_content)
            
    # def send_email(self, to_email, subject, content):
    #     """Send HTML email"""
    #     try:
    #         # Configure these with your SMTP settings
    #         smtp_server = "smtp.yahoo.com"  # Update with your SMTP server
    #         smtp_port = 587
    #         from_email = "asimo124@yahoo.com"
    #         password = "your_email_password"  # Use app password or environment variable
            
    #         msg = MimeMultipart()
    #         msg['From'] = from_email
    #         msg['To'] = to_email
    #         msg['Subject'] = subject
            
    #         msg.attach(MimeText(content, 'html'))
            
    #         server = smtplib.SMTP(smtp_server, smtp_port)
    #         server.starttls()
    #         server.login(from_email, password)
    #         text = msg.as_string()
    #         server.sendmail(from_email, to_email, text)
    #         server.quit()
            
    #         return True
    #     except Exception as e:
    #         print(f"Error sending email: {str(e)}")
    #         return False
