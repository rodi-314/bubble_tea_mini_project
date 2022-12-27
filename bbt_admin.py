from paho.mqtt import client as mqtt_client
import json

# Network Information
BROKER = 'localhost'
PORT = 12345
CLIENT_ID = 'bbt-admin'
DELIMITER = '|'

# JSON File
JSON_FILENAME = 'stock_and_menu.json'

# Global Variables
stock_items = {}


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
            print('Connected to broker!\n')

    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)
    return client


def initialise():
    """
    Initialise global variable (stock_items) using values from json file
    """
    with open(JSON_FILENAME, 'r') as json_file:
        data = json.load(json_file)
        global stock_items
        stock_items = list(data['stock'].keys())


def update_stock_and_order_number(client):
    """
    Stock and order number update loop
    :param client: MQTT client instance
    """

    def selection_validator(int_string):
        """
        :param: int_string: integer string
        :return: True if selection is valid (between 1 and the length of stock)
        """
        try:
            int(int_string)
        except ValueError:
            return False
        return 1 <= int(int_string) <= len(stock_items)

    def integer_validator(int_string):
        """
        :param int_string: integer string
        :return: True if integer >= 0
        """
        try:
            int(int_string)
        except ValueError:
            return False
        return int(int_string) >= 0

    end = False
    while not end:

        print('\n1: Order Number'
              '\n2: Stock')
        update_selection = input('What would you like to update? Enter a number: ')
        while update_selection != '1' and update_selection != '2':
            print('\nSelection is invalid.')
            update_selection = input('What would you like to update? Enter a number: ')

        # Update order number
        if update_selection == '1':
            new_order_number = input('\nWhat is the new order number? Enter a number: ')
            while not integer_validator(new_order_number):
                print('\nOrder number is invalid.')
                new_order_number = input('What is the new order number? Enter a number: ')
            client.publish('Update/OrderNo', new_order_number)

        # Update stock
        else:
            print()
            for index, name in enumerate(stock_items):
                print(f'{index + 1}: {name}')

            selection = input('Which stock would you like to update? Enter a number: ')
            while not selection_validator(selection):
                print('\nSelected drink is invalid.')
                selection = input('Which stock would you like to update? Enter a number: ')

            new_value = input('\nWhat is the new stock count? Enter a number: ')
            while not integer_validator(new_value):
                print('\nStock count is invalid.')
                new_value = input('What is the new stock count? Enter a number: ')

            ingredient = stock_items[int(selection) - 1]
            client.publish('Update/Stock', f'{ingredient}{DELIMITER}{new_value}')

        print(f'\nOrder Number/Stock updated successfully.')
        end = input('Press enter to restart, provide any input to exit: ')

    # End program
    return


def main():
    try:
        client = connect_mqtt()
        initialise()
        update_stock_and_order_number(client)
    except ConnectionRefusedError:
        print('Connection failed. Please try again.')
    except KeyboardInterrupt:
        print('Exiting program...')


if __name__ == '__main__':
    main()
