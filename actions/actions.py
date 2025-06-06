from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
from datetime import datetime

import re
import requests
import pyodbc

try:
    global_db_conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=KHANHBA;'
        'DATABASE=test_mahoaMatKhau;'
        'UID=sa;'
        'PWD=123456'
    )
except Exception as e:
    global_db_conn = None
    print(f"Lỗi kết nối DB: {e}")

class ActionAskInformation(Action):
    def name(self) -> Text:
        return "action_ask_information"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Lấy entity 'name' từ input người dùng
        name = next(tracker.get_latest_entity_values("name"), None)
        
        if name:
            dispatcher.utter_message(text=f"Hi, {name}")
        else:
            dispatcher.utter_message(text="Hi there! What's your name?")
        
        return []
class ActionCalculate(Action):
    def name(self) -> Text:
        return "action_calculate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get("text", "")
        pattern = r"([-+]?\d*\.?\d+)\s*([\+\-\*\\%])\s*([-+]?\d*\.?\d+)"
        match = re.search(pattern, user_message)

        if not match:
            dispatcher.utter_message(text="Bạn hãy nhập theo dạng: số + số hoặc số - số nhé.")
            return []

        num1 = float(match.group(1))
        operator = match.group(2)
        num2 = float(match.group(3))
        #dispatcher.utter_message(text=f"num1=:{num1}, num2=: {num2}, op=: {operator}")

        if operator == "+":
            result = num1 + num2
        elif operator == "-":
            result = num1 - num2
        elif operator == "*":
            result = num1 * num2
        elif operator == "\\":
            if(num2==0):
                dispatcher.utter_message(text="Không thể chia cho 0")
                return []
            result= num1 // num2 # chia lấy phần nguyên (10/3=3.00)
            # result= num1 / num2 chia lấy cả nguyên cả dư (10/3=3.333) 
        elif operator == "%":
            if num2 == 0:
                dispatcher.utter_message(text="Không thể chia cho 0.")
                return []
            result = num1 % num2
        else:
            dispatcher.utter_message(text="Chỉ hỗ trợ +, -, *, \\, % thôi nhé.")
            return []

        dispatcher.utter_message(text=f"Kết quả là {result}")
        return []
#ket noi sqlserver
class ActionQueryUser(Action):
    def name(self) -> Text:
        return "action_query_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global global_db_conn

        if global_db_conn is None:
            dispatcher.utter_message("Không kết nối được đến cơ sở dữ liệu.")
            return []

        try:
            # Kết nối SQL Server
            cursor = global_db_conn.cursor()
            cursor.execute("SELECT TOP 1 Username FROM Users")
            row = cursor.fetchone()

            if row:
                dispatcher.utter_message(text=f"Người dùng đầu tiên là: {row.Username}")
            else:
                dispatcher.utter_message(text="Không tìm thấy người dùng nào.")

            cursor.close()

        except Exception as e:
            dispatcher.utter_message(text=f"Lỗi kết nối: {str(e)}")

        return []

class ActionAddUser(Action):
    def name(self) -> Text:
        return "action_add_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global global_db_conn

        if global_db_conn is None:
            dispatcher.utter_message("Không kết nối được đến cơ sở dữ liệu.")
            return []

        try:
            username = tracker.get_slot("username")
            password_hash = tracker.get_slot("password_hash")
            dispatcher.utter_message(text=f"[DEBUG] Username: {username}, PasswordHash: {password_hash}")
            cursor = global_db_conn.cursor()

            cursor.execute(
                "INSERT INTO dbo.Users (Username, PasswordHash) VALUES (?, ?)",
                (username, password_hash)
            )
            global_db_conn.commit()
            dispatcher.utter_message(text=f"Đã thêm người dùng: {username}")
            cursor.close()
        except Exception as e:
            dispatcher.utter_message(text=f"Lỗi khi thêm người dùng: {str(e)}")

        return [SlotSet("username", None), SlotSet("password_hash", None)]
    
class ActionUpdateUser(Action):
    def name(self) -> Text:
        return "action_update_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global global_db_conn

        if global_db_conn is None:
            dispatcher.utter_message("Không kết nối được đến cơ sở dữ liệu.")
            return []

        try:
            id = tracker.get_slot("id")
            username = tracker.get_slot("username")
            password_hash = tracker.get_slot("password_hash")
            dispatcher.utter_message(text=f"[DEBUG]Id: {id}, Username: {username}, PasswordHash: {password_hash}")
            cursor = global_db_conn.cursor()

            cursor.execute(
                "UPDATE [dbo].[Users] SET [Username] = ?,[PasswordHash] =? WHERE [Id] = ?"
                , (username,password_hash,id)
            )
            global_db_conn.commit()
            dispatcher.utter_message(text=f"Đã update người dùng có id: {id}")
            cursor.close()
        except Exception as e:
            dispatcher.utter_message(text=f"Lỗi khi update người dùng: {str(e)}")

        return [SlotSet("username", None), SlotSet("password_hash", None), SlotSet("id",None)]

class ActionDeleteUser(Action):
    def name(self) -> Text:
        return "action_delete_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global global_db_conn

        if global_db_conn is None:
            dispatcher.utter_message("Không kết nối được đến cơ sở dữ liệu.")
            return []

        try:
            id = tracker.get_slot("id")
            dispatcher.utter_message(text=f"[DEBUG]Id: {id}")
            cursor = global_db_conn.cursor()

            cursor.execute(
                "DELETE FROM [dbo].[Users] WHERE [Id] = ?"
                , (id)
            )
            global_db_conn.commit()
            dispatcher.utter_message(text=f"Đã xóaxóa người dùng có id: {id}")
            cursor.close()
        except Exception as e:
            dispatcher.utter_message(text=f"Lỗi khi xóa người dùng: {str(e)}")

        return [SlotSet("username", None), SlotSet("password_hash", None)]

class ActionTellJoke(Action):
    def name(self) -> Text:
        return "action_tell_joke"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        url = "https://official-joke-api.appspot.com/random_joke"

        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200 and "setup" in data and "punchline" in data:
                joke = f"{data['setup']} ... {data['punchline']}"
                dispatcher.utter_message(text=joke)
            else:
                dispatcher.utter_message(text="Xin lỗi, tôi không lấy được truyện cười lúc này.")

        except Exception as e:
            dispatcher.utter_message(text="Có lỗi xảy ra khi lấy truyện cười.")
            print(f"Lỗi gọi API: {e}")

        return []
    
class ActionCheckStockStatus(Action):
    def name(self) -> Text:
        return "action_stock_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Lấy tên mã từ entity
        stock_code = tracker.get_slot("stock_code")
        dispatcher.utter_message(f"StockCode: {stock_code}")
        if not stock_code:
            dispatcher.utter_message("Bạn vui lòng cung cấp mã chứng khoán.")
            return []
        apiKey = "d10lrf1r01qlsac9tnfgd10lrf1r01qlsac9tng0"
        url = f"https://finnhub.io/api/v1/quote?symbol={stock_code.upper()}&token={apiKey}"
        response = requests.get(url)
        data = response.json()
        if data.get("d") is None:
            dispatcher.utter_message(f"Mã {stock_code.upper()} không tồn tại hoặc không có dữ liệu.")
            return [SlotSet("stock_code", None)]
        if "c" in data and "pc" in data:
            current = data["c"]
            previous = data["pc"]

            if current > previous:
                dispatcher.utter_message(f"Mã {stock_code.upper()} hôm nay tăng.")
            elif current < previous:
                dispatcher.utter_message(f"Mã {stock_code.upper()} hôm nay giảm.")
            else:
                dispatcher.utter_message(f"Mã {stock_code.upper()} không đổi.")
        else:
            dispatcher.utter_message("Không lấy được thông tin mã chứng khoán.")
        return [SlotSet("stock_code",None)] 
    
class ValidateNameForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_name_form"

    def validate_user_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate user_name value."""
        
        if slot_value and len(slot_value.strip()) > 0:
            # Capitalize first letter of each word
            formatted_name = " ".join([word.capitalize() for word in slot_value.strip().split()])
            return {"user_name": formatted_name}
        else:
            dispatcher.utter_message(text="Tên không được để trống. Vui lòng nhập tên của bạn.")
            return {"user_name": None}
           
class ActionConfirmName(Action):
    def name(self) -> Text:
        return "action_confirm_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_name = tracker.get_slot("user_name")
        
        if user_name:
            message = f"Tên của bạn là {user_name}, đúng không?"
            buttons = [
                {"title": "Đúng rồi", "payload": "/affirm"},
                {"title": "Không đúng", "payload": "/deny"}
            ]
            dispatcher.utter_message(text=message, buttons=buttons)
        
        return []
class ActionRestart(Action):
    def name(self) -> Text:
      return "action_restart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
       
       dispatcher.utter_message(text="Xin chào.Bạn tên là gì?.")
       return []
    
class ActionShowTime(Action):
    def name(self) -> Text:
        return "action_show_time"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        now =datetime.now()
        current_time = now.strftime("%H:%M:%S")
        dispatcher.utter_message(text=f"The time is :{current_time}")
        return[]
    
class ActionCheckWeather(Action):
    def name(self) -> Text:
        return "action_check_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        city = tracker.get_slot("city")
        dispatcher.utter_message(text=f"{city}")
        api_key = "7ef5f87897d77674dbe5846f9c21778a" 
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=vi"
        try:
            response = requests.get(url)

            data = response.json()
            code = data["cod"]
            dispatcher.utter_message(text=f"code {code}")
            if(code != 200):
                dispatcher.utter_message(text="Không thể lấy thông tin thời tiết lúc này.")
                return[]
            else:
            # # if data.get("main") and data.get("weather"):
                temp = data["main"]["temp"]
                weather_description = data["weather"][0]["description"]
                message = (
                    f"Thời tiết tại {city}: {weather_description}, nhiệt độ {temp}°C."
                )
                dispatcher.utter_message(text=f"{message}")
        except Exception as e:
            message = f"Lỗi khi gọi API thời tiết: {str(e)}"
            dispatcher.utter_message(text=f"Error {message}")
        return[]
