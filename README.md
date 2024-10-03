# Mini Project — Bubble Tea Ordering & Stock Management System

![image](https://github.com/user-attachments/assets/bbb9d1c3-b30f-4b40-b1e1-05c1f3b9e1df)

The purpose of this mini project is to emulate the ordering and stock management system in real bubble tea stores using the MQTT protocol. There is an electronic ordering system and stock management implemented that is constantly updated and can be dynamically edited. For more information and details, view the project presentation slides [here](https://docs.google.com/presentation/d/1WIxpvgtF3KCmu6bk_zbuvFGN2j9cvr659kE0YcljL94/edit?usp=sharing).

## Introduction
- Emulate ordering and stock management system in real bubble tea stores
- Client-server architecture
- MQTT protocol
- Features implemented:
  - Order interface for clients
  - Only allow drinks that are in stock to be ordered
  - Update stock information when a drink is ordered
  - Ability to edit stock information and order number

## Usage
### Clone Repository and Install Dependencies
```
git clone https://github.com/rodi-314/bubble_tea_mini_project.git
pip install requirements.txt
```
- All scripts use the online MQTT broker at <https://test.mosquitto.org> on port 1883, hence a local broker is not required

### Starting the Program
- Run bbt_server.py before any other scripts (i.e., bbt_admin.py, bbt_clientx.py)
- bbt_server.py has to be running for all other scripts to work
  - If bbt_server.py is down, all information (e.g., order number, stock information, etc.) will be lost
    - All information is retained as long as bbt_server.py is up

### Using the Program
- Use bbt_server.py to monitor stocks and receive orders
- Use bbt_clientx.py to purchase items (bbt_clientx.py can be duplicated to simulate more ordering machines)
- Use bbt_admin.py to update the order number or stocks

## Screenshots

### Monitoring Interface (Start Screen)
![image](https://github.com/user-attachments/assets/86ac2430-2875-49c5-8d43-62b1affdbb3c)

### Monitoring Interface (After 9 Orders)
![image](https://github.com/user-attachments/assets/620f5b4a-82fd-4f0f-a98d-f3f9062fdcad)

### Corresponding Ordering Interface (After 9 Orders)
![image](https://github.com/user-attachments/assets/b7b02034-31e9-4825-b72d-ca14c2db89cd)

## Version 1

![image](https://github.com/user-attachments/assets/53566262-c312-42e8-93e4-883cd3868edd)

- Each machine has its own global variables for stock, menu, and order number
- Updating stock or order number (admin):
  - New variables published to broker
    - Sent to other machines and the admin itself
    - Upon receiving the update, global variables are updated (stock, order number)
- Ordering a drink (client):
  - Client checks stock locally if drink is available
  - If drink is available:
    - New variables published to other machines
    - Upon receiving the update, global variables are updated (stock, order number)
    - Order published

### Shortcomings
- Inefficiency:
  - Clients store a lot of information (menu, stock, order number)
  - Clients check if drinks are still available
  - Many MQTT topics used for each ingredient in stock, orders, and order number
- Clients will be out of sync when restarted
- Orders sent at the same time will cause stock and order number to be updated incorrectly
- Stock and menu must be updated on all machines if edited
- Sensitive information (stock) can be accessed by clients

## Version 2

![image](https://github.com/user-attachments/assets/0cf22215-e1dc-4161-8d80-f0be98b40239)

- Clients only store information on menu and availability
- Server stores all information – menu and availability, stock, order number
- Updating stock or order number (admin):
  - New variables published to broker
    - Sent to other machines and the admin itself
    - Upon receiving the update, global variables are updated (stock, order number)
- Ordering a drink (client):
  - Client sends a purchase request to server
    - Server checks stock locally if drink is available
    - If drink is available:
      - Server updates global variables (stock, order number, menu and availability)
      - Server sends approved reply with order number to client
      - Server sends update for menu and availability to all clients
    - If drink is out of stock:
      - Server sends rejected reply to client

### Improvements
- Improved efficiency:
  - Clients only store information on menu and availability
  - Checking is done by the server
  - Only 3 MQTT topics used – Order/Request, Order/Reply, Menu/Availability
- Clients will be in sync when restarted
- Orders made at the same time will not cause incorrect updates
  - Server can only process one request at a time
- Stock and menu only has to be updated on server if edited
- Sensitive information (stock) cannot be accessed by clients
