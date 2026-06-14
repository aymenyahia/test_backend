import requests

BASE_URL = "http://localhost:5000/api"

def test_users():
    print("=" * 40)
    print("TESTING USERS API")
    print("=" * 40)
    
    # GET all users
    r = requests.get(f"{BASE_URL}/users")
    print(f"GET /users: {r.status_code}")
    print(r.json())
    
    # CREATE user
    user_data = {
        "matricule": "M001",
        "name": "John",
        "family_name": "Doe",
        "category": 1,
        "grade": 1,
        "user_name": "johndoe",
        "password": "secret123",
        "profil_pic_url": ""
    }
    r = requests.post(f"{BASE_URL}/users", json=user_data)
    print(f"\nPOST /users: {r.status_code}")
    print(r.json())
    
    # GET single user
    r = requests.get(f"{BASE_URL}/users/M001")
    print(f"\nGET /users/M001: {r.status_code}")
    print(r.json())
    
    # UPDATE user
    r = requests.put(f"{BASE_URL}/users/M001", json={"name": "Johnny"})
    print(f"\nPUT /users/M001: {r.status_code}")
    print(r.json())
    
    # SEARCH users
    r = requests.get(f"{BASE_URL}/search/users", params={"q": "John"})
    print(f"\nGET /search/users?q=John: {r.status_code}")
    print(r.json())

def test_grades():
    print("\n" + "=" * 40)
    print("TESTING GRADES API")
    print("=" * 40)
    
    # GET all
    r = requests.get(f"{BASE_URL}/grades")
    print(f"GET /grades: {r.status_code}")
    print(r.json())
    
    # CREATE
    r = requests.post(f"{BASE_URL}/grades", json={"grade_name": "Manager"})
    print(f"\nPOST /grades: {r.status_code}")
    print(r.json())
    
    # GET single
    r = requests.get(f"{BASE_URL}/grades/1")
    print(f"\nGET /grades/1: {r.status_code}")
    print(r.json())

def test_tasks():
    print("\n" + "=" * 40)
    print("TESTING TASKS API")
    print("=" * 40)
    
    # CREATE task
    task_data = {
        "title": "Fix login bug",
        "description": "Users can't login with special characters",
        "dead_line": "2026-06-15T10:00:00",
        "creater": "M001",
        "state": 1
    }
    r = requests.post(f"{BASE_URL}/tasks", json=task_data)
    print(f"POST /tasks: {r.status_code}")
    print(r.json())
    
    # GET all
    r = requests.get(f"{BASE_URL}/tasks")
    print(f"\nGET /tasks: {r.status_code}")
    print(r.json())

def test_sql():
    print("\n" + "=" * 40)
    print("TESTING SQL API")
    print("=" * 40)
    
    # SELECT query
    r = requests.post(f"{BASE_URL}/sql", json={"query": "SELECT * FROM users"})
    print(f"POST /sql (SELECT): {r.status_code}")
    print(r.json())
    
    # Complex JOIN
    query = """
        SELECT u.name, u.family_name, g.grade_name, c.category_name 
        FROM users u
        JOIN grades g ON u.grade = g.grade_id
        JOIN categories c ON u.category = c.category_id
    """
    r = requests.post(f"{BASE_URL}/sql", json={"query": query})
    print(f"\nPOST /sql (JOIN): {r.status_code}")
    print(r.json())

def test_chats():
    print("\n" + "=" * 40)
    print("TESTING CHATS API")
    print("=" * 40)
    
    # Create P2P chat
    r = requests.post(f"{BASE_URL}/p2p-chats", json={"first_user": "M001", "second_user": "M002"})
    print(f"POST /p2p-chats: {r.status_code}")
    print(r.json())
    
    # Get P2P chats
    r = requests.get(f"{BASE_URL}/p2p-chats")
    print(f"\nGET /p2p-chats: {r.status_code}")
    print(r.json())
    
    # Send message
    r = requests.post(f"{BASE_URL}/p2p-chats/1/messages", json={"user_id": "M001", "content": "Hello!"})
    print(f"\nPOST /p2p-chats/1/messages: {r.status_code}")
    print(r.json())
    
    # Get messages
    r = requests.get(f"{BASE_URL}/p2p-chats/1/messages")
    print(f"\nGET /p2p-chats/1/messages: {r.status_code}")
    print(r.json())

if __name__ == '__main__':
    test_grades()
    test_users()
    test_tasks()
    test_chats()
    test_sql()
    print("\n" + "=" * 40)
    print("ALL TESTS COMPLETED")
    print("=" * 40)