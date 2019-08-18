import discord  #TODO: FIX REMOVE!!!
import re
import numpy as np
from yaml import load, dump
# importing yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# loading in the yaml files
with open("coordinates.yaml") as coordinates_file:
    coordinates = load(coordinates_file, Loader=Loader)

with open("channels.yaml") as channels_file:
    channels = load(channels_file, Loader=Loader)

with open("messages.yaml") as messages_file:
    messages = load(messages_file, Loader=Loader)

with open("patterns.yaml") as patterns_file:
    patterns = load(patterns_file, Loader=Loader)


# getting the bot online
client = discord.Client()
token = 'NjA1OTc2MDAwODQwNTk3NTA1.XUXCJA.4W57fayO7_DX94pIrixG6LQkClk'


def get_locations(server_id, message, location_name):
    """
    This function constructs and returns a tuple with the lists of the locations, then the private ones, then the public ones.
    """
    locations = []
    private_locations = []
    public_locations = []

    try:
        for location in coordinates[server_id][str(message.author.discriminator)][location_name]:
            locations += [location]
            private_locations += [location]
    except KeyError or TypeError:
        pass

    try:
        for location in coordinates[server_id]['all'][location_name]:
            locations += [location]
            public_locations += [location]
    except KeyError or TypeError:
        pass

    return locations, private_locations, public_locations


def file_update(filename, new_dict):
    """
    A simple function that will update the file stored under 'filename'
    by replacing it with the data stored in new_dict.
    """
    with open(filename, 'w') as file:
        dump(new_dict, file)


def dist(p1, p2):
    """
    returns the distance between points p1 and p2
    """
    distance = 0
    if len(p1) == len(p2):
        for point in range(len(p1)):
            distance += abs(p1[point] - p2[point])
    elif len(p1) > len(p2):
        distance = abs(p1[0] - p2[0]) + abs(p1[2] - p2[1])
    elif len(p1) < len(p2):
        distance = abs(p1[0] - p2[0]) + abs(p1[1] - p2[2])
    return distance


@client.event
async def on_message(message):  # called when a player sends a message in chat
    server = message.guild
    server_id = server.id  # server is a server object while server_id is an integer unique to the server

    if re.match(r"(nate).*", message.content) is None:
        return

    if message.author.name != 'Coordinates Bot':
        # retrieves or generates the channel to send the message in
        try:
            channel = client.get_channel(channels[server_id][str(message.author.discriminator)])
        except KeyError or TypeError:
            overwrites = {  # TODO: make it so server owner can't access
                server.default_role: discord.PermissionOverwrite(read_messages=False),
                message.author: discord.PermissionOverwrite(read_messages=True),
                server.me: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await server.create_text_channel(message.author.name + '-coordinates', overwrites=overwrites)
            await channel.send(messages['welcome'])

            try:
                channels[server_id].update({str(message.author.discriminator): channel.id})
            except KeyError or TypeError:
                channels.update({server_id: {str(message.author.discriminator): channel.id}})
            file_update("channels.yaml", channels)
    else:
        return

    message_pattern = re.compile(patterns['message'])
    message_match = re.match(message_pattern, message.content)  # the regex is used to parse the first

    if message_match is None:
        channel.send(messages['syntax_error'].format(message.content, ''))

    # two words of the message, the activation word and the command. It will give us the parameters for later
    command = message_match.group(2)
    parameters = message_match.group(3)

    if command == 'add':  # TODO: add support for dimensions and have it default to overworld.
        # this command should be called like this:
        # 'nate add <private/public/None> <name> x y z'
        # the private or public aren't required and will default to public and the y coordinate is not needed
        add_pattern = re.compile(patterns['add'])
        add_match = re.match(add_pattern, parameters)  # another regex for parsing the parameters for this function

        if add_match is None:
            await channel.send(messages['syntax_error'].format(message.content, ' add'))
            return

        # figuring out where to add the coordinates under
        if add_match.group(1) == 'private':
            owner = str(message.author.discriminator)
        else:
            owner = 'all'

        location_name = add_match.group(2)

        # generating a tuple with the coordinate values
        if add_match.group(5) == '':
            location_coordinates = (int(add_match.group(3)), int(add_match.group(4)))
        else:
            location_coordinates = (int(add_match.group(3)), int(add_match.group(4)), int(add_match.group(5)))

        # tries to place coordinates under location but adds new indices if not already there
        try:
            coordinates[server_id][owner][location_name] += [location_coordinates]
        except KeyError:
            try:
                coordinates[server_id][owner].update({location_name: [location_coordinates]})
            except KeyError:
                try:
                    coordinates[server_id].update({owner: {location_name: [location_coordinates]}})
                except KeyError:
                    coordinates.update({server_id: {owner: {location_name: [location_coordinates]}}})

        file_update("coordinates.yaml", coordinates)

        # decides which of the two messages to send
        if owner == 'all':
            await channel.send(messages['added_public'].format(location_name, location_coordinates[0],
                                                               (str(location_coordinates[-2])+' ') *
                                                               (len(location_coordinates) == 3),
                                                               location_coordinates[-1]))
        else:
            await channel.send(messages['add_private'].format(location_name, location_coordinates[0],
                                                              (str(location_coordinates[-2])+' ') *
                                                              (len(location_coordinates) == 3),
                                                              location_coordinates[-1]))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    elif command == 'remove':  # TODO: add the coordinates being optional.
        remove_pattern = re.compile(patterns['remove'])
        remove_match = re.match(remove_pattern, parameters)

        if remove_match is None:
            await channel.send(messages['syntax_error'].format(message.content, ' remove'))
            return

        location_name = remove_match.group(1)
        owner = str(message.author.discriminator)

        if remove_match.group(2) == remove_match.group(3) == remove_match.group(4) == '':
            return
        if remove_match.group(3) == remove_match.group(4) == '':
            await channel.send(messages['syntax_error'].format(message.content, ' remove'))
            return
        elif remove_match.group(4) == '':
            location_coordinates = (int(remove_match.group(2)), int(remove_match.group(3)))
        else:
            location_coordinates = (int(remove_match.group(2)), int(remove_match.group(3)),
                                    int(remove_match.group(4)))


        if message.author == server.owner:
            locations, private_locations, public_locations = get_locations(server_id, message, location_name)

            try:
                if len(coordinates[server_id][owner][location_name]) > 0:
                    coordinates[server_id][owner][location_name].remove(location_coordinates)
                    file_update("coordinates.yaml", coordinates)

                    await channel.send("I have removed the coordinates in your branch under the name '{}'"
                                       " at the location {} {}{}.".format(location_name, location_coordinates[0],
                                                                          (str(location_coordinates[-2])+' ') *
                                                                          (len(location_coordinates) == 3),
                                                                          location_coordinates[-1]))

                elif len(coordinates[server_id][owner][location_name]) == 0:
                    try:
                        if len(coordinates[server_id]['all'][location_name]) > 0:
                            coordinates[server_id]['all'][location_name].remove(location_coordinates)
                            file_update("coordinates.yaml", coordinates)

                            await channel.send(
                                "I have removed the coordinates in the public branch under the name '{}'"
                                " at the location {} {}{}.".format(location_name, location_coordinates[0],
                                                                   (str(location_coordinates[-2])+' ') *
                                                                   (len(location_coordinates) == 3),
                                                                   location_coordinates[-1]))
                        elif len(coordinates[server_id]['all'][location_name]) == 0:
                            await channel.send(
                                "I was unable to find any coordinates under any branch with the name '{}'"
                                " and the coordinates {} {}{}.".format(location_name, location_coordinates[0],
                                                                  (str(location_coordinates[-2])+' ') *
                                                                  (len(location_coordinates) == 3),
                                                                  location_coordinates[-1]))
                    except KeyError:
                        await channel.send(
                            "I was unable to find any coordinates under any branch with the name '{}'"
                            " and the coordinates {} {}{}.".format(location_name, location_coordinates[0],
                                                              (str(location_coordinates[-2])+' ') *
                                                              (len(location_coordinates) == 3),
                                                              location_coordinates[-1]))
            except KeyError:
                try:
                    if len(coordinates[server_id]['all'][location_name]) > 0:
                        coordinates[server_id]['all'][location_name].remove(location_coordinates)
                        file_update("coordinates.yaml", coordinates)
                        await channel.send(
                            "I have removed the coordinates in the public branch under the name '{}'"
                            " at the location {} {}{}.".format(location_name, location_coordinates[0],
                                                          (str(location_coordinates[-2])+' ') *
                                                          (len(location_coordinates) == 3),
                                                          location_coordinates[-1]))
                    elif len(coordinates[server_id]['all'][location_name]) == 0:
                        await channel.send(
                            "\nI was unable to find any coordinates under your branch with the name '{}'"
                            " and the coordinates {} {}{}."
                            " If the coordinates you were looking to remove are located"
                            " in the public branch you do not have sufficient permissions."
                            " Ask the server owner to remove something from the public branch."
                            "".format(location_name, location_coordinates[0],
                                      (str(location_coordinates[-2])+' ') *
                                      (len(location_coordinates) == 3),
                                      location_coordinates[-1]))
                except KeyError:
                    await channel.send(
                        "\nI was unable to find any coordinates under your branch with the name '{}'"
                        " and the coordinates {} {}{}. "
                        " If the coordinates you were looking to remove are located"
                        " in the public branch you do not have sufficient permissions."
                        " Ask the server owner to remove something from the public branch."
                        "".format(location_name, location_coordinates[0],
                                  (str(location_coordinates[-2])+' ') *
                                  (len(location_coordinates) == 3),
                                  location_coordinates[-1]))

            else:
                try:
                    if len(coordinates[server_id][owner][location_name]) > 0:
                        coordinates[server_id][owner][location_name].remove(location_coordinates)
                        file_update("coordinates.yaml", coordinates)
                        await channel.send("I have removed the coordinates in your branch under the name '{}'"
                                           " at the location {} {}{}.".format(location_name, location_coordinates[0],
                                                                         (str(location_coordinates[-2])+' ') *
                                                                         (len(location_coordinates) == 3),
                                                                         location_coordinates[-1]))
                    elif len(coordinates[server_id][owner][location_name]) == 0:
                        await channel.send(
                            "\nI was unable to find any coordinates under your branch with the name '{}'"
                            " and the coordinates {} {}{}."
                            " If the coordinates you were looking to remove are located"
                            " in the public branch you do not have sufficient permissions."
                            " Ask the server owner to remove something from the public branch."
                            "".format(location_name, location_coordinates[0],
                                      (str(location_coordinates[-2])+' ') *
                                      (len(location_coordinates) == 3),
                                      location_coordinates[-1]))
                except KeyError or TypeError:
                    await channel.send(
                        "\nI was unable to find any coordinates under your branch with the name '{}'"
                        " and the coordinates {} {}{}."
                        " If the coordinates you were looking to remove are located"
                        " in the public branch you do not have sufficient permissions."
                        " Ask the server owner to remove something from the public branch."
                        "".format(location_name, location_coordinates[0],
                                  (str(location_coordinates[-2])+' ') *
                                  (len(location_coordinates) == 3),
                                  location_coordinates[-1]))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    elif command == 'list':
        list_pattern = patterns['list']
        list_match = re.match(list_pattern, parameters)

        if list_match is None:
            await channel.send(messages['syntax_error'].format(message.content, ' list'))
            return

        location_name = list_match.group(1)

        if list_match.group(2) != '':
            if list_match.group(4) != '':
                player_coordinates = (int(list_match.group(2)), int(list_match.group(3)), int(list_match.group(4)))
            else:
                player_coordinates = (int(list_match.group(2)), int(list_match.group(3)))
        else:
            player_coordinates = None

        if location_name != '':
            if player_coordinates is not None:
                locations = get_locations(server_id, message, location_name, private=True, public=True)
                if len(locations) == 0:
                    await channel.send(messages['list_none'].format(location_name))
                else:
                    shortest = None
                    shortest_dist = np.inf
                    for location in locations:
                        if dist(player_coordinates, location) < shortest_dist:
                            shortest = location
                            shortest_dist = dist(player_coordinates, location)
                    await channel.send(messages['list_closest'].format(location_name, shortest_dist, 's'*(shortest_dist != 1), shortest))
            else:
                locations = get_locations(server_id, message, location_name, private=True, public=True)
                await channel.send(messages['list_all'].format(str(len(locations)), 's'*(len(locations) != 1), location_name))
                for location in locations:
                    await channel.send(messages['list_coordinates'].format(location_name, location))
        else:
            private_location_names = []
            public_location_names = []
            try:
                for name in coordinates[server_id][str(message.author.discriminator)]:
                    if len(coordinates[server_id][str(message.author.discriminator)][name]) > 0:
                        private_location_names += [name]
            except KeyError:
                pass
            try:
                for name in coordinates[server_id]['all']:
                    if len(coordinates[server_id]['all'][name]) > 0:
                        public_location_names += [name]
            except KeyError:
                pass
            await channel.send(messages['list_private'].format(len(private_location_names),
                                         's'*(len(private_location_names) != 1),
                                         ':' * (len(private_location_names) != 0),
                                         '.' * (len(private_location_names) == 0)))

            for name in private_location_names:
                await channel.send(messages['list_name'].format(name))

            await channel.send(messages['list_public'].format(len(public_location_names),
                                                        's' * (len(public_location_names) != 1),
                                                        ':' * (len(public_location_names) != 0),
                                                        '.' * (len(public_location_names) == 0)))
            for name in public_location_names:
                await channel.send(messages['list_name'].format(name))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    elif command == 'clear':
        clear_pattern = patterns['clear']
        clear_match = re.match(clear_pattern, parameters)

        if clear_match is None:
            await channel.send(messages['syntax_error'].format(message.content, ' clear'))
            return

        branch = clear_match.group(1)

        if branch == 'public' and message.author == server.owner:
            try:
                if len(coordinates[server_id]['all']) == 0:
                    await channel.send(messages['clear_none_public'])
                else:
                    coordinates[server_id]['all'] = []
                    file_update("coordinates.yaml", coordinates)
                    await channel.send(messages['clear_public'])
            except KeyError or TypeError:
                await channel.send(messages['clear_none_public'])
        elif branch == 'public':
            await channel.send(messages['clear_public_fail'])
        elif branch == 'private' or branch == '':
            try:
                if len(coordinates[server_id][str(message.author.discriminator)]) == 0:
                    await channel.send(messages['clear_none_private'])
                else:
                    coordinates[server_id][str(message.author.discriminator)] = []
                    file_update("coordinates.yaml", coordinates)
                    await channel.send(messages['clear_private'])
            except KeyError or TypeError:
                await channel.send(messages['clear_none_private'])
        else:
            await channel.send(messages['syntax_error'].format(message.content))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    elif command == 'help':
        help_pattern = patterns['help']
        help_match = re.match(help_pattern, parameters)

        if help_match is None:
            await channel.send(messages['syntax_error'].format(message.content, ' help'))
            return

        help_command = help_match.group(1)
        if help_command == '':
            await channel.send(messages['help'])
        elif help_command == 'add':
            await channel.send(messages['add_help'])
        elif help_command == 'remove':
            await channel.send(messages['remove_help'])
        elif help_command == 'list':
            await channel.send(messages['list_help'])
        elif help_command == 'clear':
            await channel.send(messages['clear_help'])
        elif help_command == 'help':
            await channel.send(messages['help_help'])
        else:
            await channel.send(messages['not_command'].format(help_command))
    else:
        await channel.send(messages['not_command'].format(command))

client.run(token)
