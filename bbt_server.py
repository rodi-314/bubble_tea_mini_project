from paho.mqtt import client as mqtt_client
import json
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import FixedLocator
import time

# Network Information
BROKER = 'localhost'
PORT = 12345
CLIENT_ID = 'bbt-server'
DELIMITER = '|'
WAIT_FOR_CONNECTION = 1  # seconds

# JSON File
JSON_FILENAME = 'stock_and_menu.json'

# Monitoring Interface Constants
# Update Interval
UPDATE_INTERVAL = 1000  # ms
# Show Last X Orders
X = 7
# Window Configuration
FIGURE_SIZE = (10, 7.5)
DPI = 100
# Text
WINDOW_TITLE = 'Bubble Tea Server Monitoring Interface'
LOADING_STATISTICS_TEXT = 'Loading Statistics...'
WARNING_TEXT = 'Warning: Closing this window will halt the server!'
STOCK_STATISTICS_TITLE = 'Stock Statistics'
STOCK_UNITS = 'Millilitres /ml'
MENU_AVAILABILITY_TITLE = 'Menu Availability'
LAST_X_ORDERS_TITLE = f'Last {X} Orders'
TEXT_ROTATION = 30  # degrees
# Colours
WARNING_COLOUR = 'tab:red'
STOCK_COLOUR = 'tab:blue'
AVAILABLE_COLOUR = 'tab:green'
OUT_OF_STOCK_COLOUR = 'tab:red'
ORDERS_COLOUR = 'tab:purple'
BACKGROUND_COLOUR = 'papayawhip'

# Global Variables
stock = {}
menu = {}
order_number = 1
menu_availability = {}
last_x_orders = ['-'] * X


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


def check_availability(drink):
    """
    Check if there are enough ingredients in the stock to make the drink
    :param drink: name of drink
    :return: True if drink is available, False otherwise
    """
    recipe = menu[drink]
    for ingredient in recipe:
        if stock[ingredient] < recipe[ingredient]:
            return False
    return True


def get_menu_availability():
    """
    Creates a dictionary with:
    Keys: drink names
    Values: True if drink is available, False if it is out of stock
    :return: menu_availability dictionary
    """
    global menu_availability
    for drink in menu:
        menu_availability[drink] = check_availability(drink)
    return menu_availability


def initialise(client):
    """
    Initialise global variables (stock, menu) using values from json file
    Publishes the current menu and availability to all clients
    :param client: MQTT client instance
    """
    with open(JSON_FILENAME, 'r') as json_file:
        data = json.load(json_file)
        global stock, menu
        stock, menu = data['stock'], data['menu']
    client.publish('Menu/Availability', f'{get_menu_availability()}', retain=True)


def reduce_stock(drink):
    """
    Reduces the stock when a drink is ordered
    :param drink: name of drink
    """
    recipe = menu[drink]
    for ingredient in recipe:
        stock[ingredient] -= recipe[ingredient]


def on_message(client, _userdata, msg):
    """
    Verifies order requests sent from clients and prints orders
    When an order request is received, the stock is checked to find out whether the drink is available
    Publish approved reply if drink is available, rejected reply if drink is out of stock
    :param client: MQTT client instance
    :param _userdata: private user data
    :param msg: MQTT client message instance
    """
    global order_number
    if msg.topic == 'Order/Request':
        # Parse message received from Order/Request
        client_id, drink = msg.payload.decode().split(DELIMITER)

        # If drink is available, approve request
        if check_availability(drink):
            reduce_stock(drink)
            # client_id and order_number sent for approved reply
            client.publish('Order/Reply', f'{client_id}{DELIMITER}{order_number}')
            # Publish new menu availability to all clients
            client.publish('Menu/Availability', f'{get_menu_availability()}', retain=True)

            # Update last x orders
            last_x_orders.pop(0)
            last_x_orders.append(f'\nOrder {order_number}: {drink}\n')

            order_number += 1

        # If drink is out of stock, reject request
        else:
            # Only client_id sent for rejected reply
            client.publish('Order/Reply', f'{client_id}')

    elif msg.topic == 'Update/OrderNo':
        order_number = int(msg.payload.decode())

    else:
        # Parse message received from Update/Stock
        ingredient, new_value = msg.payload.decode().split(DELIMITER)
        # Update stock
        stock[ingredient] = int(new_value)
        # Publish new menu availability to all clients
        client.publish('Menu/Availability', f'{get_menu_availability()}', retain=True)


def display_statistics():
    """
    Displays stock and menu availability statistics, and last x orders using matplotlib
    """
    # Figure Configuration
    fig = plt.figure(WINDOW_TITLE, figsize=FIGURE_SIZE, dpi=DPI)
    fig.suptitle(WINDOW_TITLE, fontweight='bold')
    fig.subplots_adjust(left=0.1, hspace=0.75)
    fig.patch.set_facecolor(BACKGROUND_COLOUR)

    # 1st Graph: Stock Statistics
    ax1 = fig.add_subplot(4, 1, 1)
    ax1.axis('off')
    # Loading text
    ax1.text(x=0.5,
             y=0.5,
             s=LOADING_STATISTICS_TEXT,
             horizontalalignment='center',
             verticalalignment='center',
             fontsize='large')

    # 2nd Graph: Menu Availability
    ax2 = fig.add_subplot(4, 1, 2)
    ax2.axis('off')
    # Loading text
    ax2.text(x=0.5,
             y=0.5,
             s=LOADING_STATISTICS_TEXT,
             horizontalalignment='center',
             verticalalignment='center',
             fontsize='large')

    # 3rd Graph: Last X Orders
    ax3 = fig.add_subplot(3, 2, 5)
    ax3.axis('off')
    # Loading text
    ax3.text(x=0.5,
             y=0.5,
             s=LOADING_STATISTICS_TEXT,
             horizontalalignment='center',
             verticalalignment='center',
             fontsize='large')

    # Warning
    ax4 = fig.add_subplot(3, 2, 6)
    ax4.axis('off')
    # Warning text
    text_box = dict(color=WARNING_COLOUR,
                    alpha=0.8)
    ax4.text(x=0.5,
             y=0.5,
             s=WARNING_TEXT,
             horizontalalignment='center',
             verticalalignment='center',
             fontsize='large',
             color='white',
             bbox=text_box)

    def update_statistics(_frame):
        """
        Updates statistics charts every UPDATE_INTERVAL
        :param _frame:
        :return: bar_container1, bar_container2, bar_container3
        """
        # 1st Graph: Stock Statistics
        ax1.clear()
        ax1.set_title(STOCK_STATISTICS_TITLE)
        bar_container1 = ax1.bar(list(stock.keys()),
                                 list(stock.values()),
                                 color=STOCK_COLOUR)
        ax1.bar_label(bar_container1,
                      label_type='center',
                      color='white')
        ax1.set_ylabel(STOCK_UNITS)
        # Rotate tick labels
        ax1_ticks_location = ax1.get_xticks()
        ax1.xaxis.set_major_locator(FixedLocator(ax1_ticks_location))
        ax1.set_xticklabels(ax1.get_xticklabels(),
                            rotation=TEXT_ROTATION,
                            ha='right')

        # 2nd Graph: Menu Availability
        ax2.clear()
        ax2.set_title(MENU_AVAILABILITY_TITLE)
        bar_container2 = ax2.bar(list(menu_availability.keys()),
                                 [1] * len(menu_availability),
                                 color=[AVAILABLE_COLOUR if drink
                                        else OUT_OF_STOCK_COLOUR for drink in menu_availability.values()])
        ax2.bar_label(bar_container2,
                      labels=['Available' if drink else 'Out of Stock' for drink in menu_availability.values()],
                      label_type='center',
                      color='white',
                      rotation=90)
        ax2.yaxis.set_visible(False)
        # Rotate tick labels
        ax2_ticks_location = ax2.get_xticks()
        ax2.xaxis.set_major_locator(FixedLocator(ax2_ticks_location))
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=TEXT_ROTATION, ha='right')

        # 3rd Graph: Last X Orders
        ax3.clear()
        ax3.set_title(LAST_X_ORDERS_TITLE)
        bar_container3 = ax3.barh([integer for integer in range(X)],
                                  [1] * X,
                                  color=ORDERS_COLOUR)
        ax3.bar_label(bar_container3,
                      labels=reversed(last_x_orders),
                      label_type='center',
                      color='white')
        ax3.axis('off')

        return bar_container1, bar_container2, bar_container3

    # Plotting the graph
    _animation = FuncAnimation(fig, update_statistics, interval=UPDATE_INTERVAL)
    plt.show()


def main():
    try:
        client = connect_mqtt()
        initialise(client)
        client.subscribe([('Order/Request', 0), ('Update/#', 0)])
        client.on_message = on_message
        threading.Thread(target=client.loop_forever, daemon=True).start()
        time.sleep(WAIT_FOR_CONNECTION)  # Wait for connection to broker
        display_statistics()
        print('Exiting program...')
    except ConnectionRefusedError:
        print('Connection failed. Please try again.')
    except KeyboardInterrupt:
        print('Exiting program...')


if __name__ == '__main__':
    main()
