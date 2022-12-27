from paho.mqtt import client as mqtt_client
import threading
import time

# Network Information
BROKER = 'localhost'
PORT = 12345
CLIENT_ID = 'bbt-client-2'
DELIMITER = '|'
WAIT_FOR_CONNECTION = 1  # seconds
WAIT_FOR_REPLY = 0.1  # seconds

# Global Variables
menu_availability = {}
order_number = 'NEW ORDER'
received_reply = False


def connect_mqtt():
    """
    Connects to the MQTT broker
    :return: MQTT client instance
    """

    def on_connect(_client, _userdata, _flags, rc):
        """
        :param _client: MQTT client instance
        :param _userdata: private user data
        :param _flags: response flags sent by broker
        :param rc: return code for connection result
        :return:
        """
        if rc != 0:
            print(f'Return Code {rc}: {mqtt_client.connack_string(rc)}\n')
        else:
            print('Connected to broker!')

    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)
    return client


def on_message(_client, _userdata, msg):
    """
    Updates global variable (menu_availability) when updates are published
    Checks order replies for approval or rejection
    :param _client: MQTT client instance
    :param _userdata: private user data
    :param msg: MQTT client message instance
    """
    if msg.topic == 'Menu/Availability':
        global menu_availability
        menu_availability = eval(msg.payload.decode())

    # Checks if Order/Reply message is directed at this client
    elif msg.payload.decode().startswith(CLIENT_ID):
        global order_number, received_reply
        # If the order is approved (message contains CLIENT_ID and order number)
        if msg.payload.decode() != CLIENT_ID:
            order_number = int(msg.payload.decode().split(DELIMITER)[-1])
        # If the order is rejected (message contains CLIENT_ID only)
        else:
            order_number = 'REJECTED'
        received_reply = True


def print_menu_availability():
    """
    Prints the menu and the availability of the drinks
    """
    print()
    for index, drink in enumerate(menu_availability):
        if menu_availability[drink]:
            print(f'{index + 1}: {drink} [Available]')
        else:
            print(f'{index + 1}: {drink} [Out of Stock]')


def selection_validator(int_string):
    """
    :param: int_string: integer string
    :return: True if selection is valid (between 1 and the length of the menu)
    """
    try:
        int(int_string)
    except ValueError:
        return False
    return 1 <= int(int_string) <= len(menu_availability)


def order(client):
    """
    Order interface loop
    :param client: MQTT client instance
    :return:
    """
    # Wait for menu and availability to be updated by server before allowing orders
    while not menu_availability:
        print('Waiting for menu and availability to be updated...')
        time.sleep(1)
    print('Menu and availability updated!')

    end = False
    while not end:

        global order_number
        # Start and restart order loop for new orders and rejected orders respectively
        while order_number == 'NEW ORDER' or order_number == 'REJECTED':

            if order_number == 'REJECTED':
                print('\nDrink is out of stock. Please select another drink.')
            print_menu_availability()

            # Prompts user to select a valid drink
            selection = input('\nWhat would you like to order? Enter a number: ')
            while not selection_validator(selection):
                print('\nSelected drink is invalid.')
                print_menu_availability()
                selection = input('\nWhat would you like to order? Enter a number: ')

            # Convert selection number to name of drink and publish order request
            drink = list(menu_availability)[int(selection) - 1]
            client.publish('Order/Request', f'{CLIENT_ID}{DELIMITER}{drink}')

            # Wait for order reply
            global received_reply
            while not received_reply:
                time.sleep(WAIT_FOR_REPLY)
            received_reply = False

        print(f'\nOrder sent successfully. Your order number is {order_number}.')
        order_number = 'NEW ORDER'
        end = input('Press enter to restart, provide any input to exit: ')

    return


def main():
    try:
        client = connect_mqtt()
        client.subscribe([('Order/Reply', 0), ('Menu/Availability', 0)])
        client.on_message = on_message
        threading.Thread(target=client.loop_forever, daemon=True).start()
        time.sleep(WAIT_FOR_CONNECTION)  # Wait for connection to broker
        order(client)
    except ConnectionRefusedError:
        print('Connection failed. Please try again.')
    except KeyboardInterrupt:
        print('\n\nExiting program...')


if __name__ == '__main__':
    main()
