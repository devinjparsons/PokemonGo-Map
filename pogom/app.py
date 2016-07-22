#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from datetime import datetime
from geopy.geocoders import GoogleV3

from . import config
from .models import Pokemon, Gym, Pokestop


class Pogom(Flask):
    def __init__(self, import_name, **kwargs):
        super(Pogom, self).__init__(import_name, **kwargs)
        self.json_encoder = CustomJSONEncoder
        self.route("/", methods=['GET'])(self.fullmap)
        self.route("/raw_data", methods=['GET'])(self.raw_data)
        self.route("/next_loc", methods=['POST'])(self.next_loc)
        self.route("/next_address", methods=['GET'])(self.next_address)
        self.route("/update_notification_email", methods=['GET'])(self.update_notification_email)
        self.route("/update_notification_list", methods=['GET'])(self.update_notification_list)
        self.rout("/get_config", methods=['GET'])(self.get_config)

    def fullmap(self):
        return render_template('map.html',
                               lat=config['ORIGINAL_LATITUDE'],
                               lng=config['ORIGINAL_LONGITUDE'],
                               gmaps_key=config['GMAPS_KEY'],
                               lang=config['LOCALE'])

    def raw_data(self):
        d = {}
        if request.args.get('pokemon', 'true') == 'true':
            d['pokemons'] = Pokemon.get_active()

        if request.args.get('pokestops', 'false') == 'true':
            d['pokestops'] = Pokestop.get_all()

        if request.args.get('gyms', 'true') == 'true':
            d['gyms'] = Gym.get_all()

        return jsonify(d)

    def next_loc(self):
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)

        if not (lat and lon):
            print('[-] Invalid next location: %s,%s' % (lat, lon))
            return 'bad parameters', 400
        else:
            config['ORIGINAL_LATITUDE'] = lat
            config['ORIGINAL_LONGITUDE'] = lon
            return 'ok, location set to: %s,%s' % (lat, lon)

    def next_address(self):
        address = request.args.get('address', type=str)

        if not address:
            print('[-] Invalid next address: %s' % address)
            return 'bad parameters', 400
        else:
            geolocator = GoogleV3()
            loc = geolocator.geocode(address)
            config['ORIGINAL_LATITUDE'] = loc.latitude
            config['ORIGINAL_LONGITUDE'] = loc.longitude
            return 'ok, next address set to {0}'.format(loc.address.encode('utf-8'))

    def update_notification_email(self):
        email = request.args.get('email', type=str)
        config['NOTIFICATION_EMAIL'] = email
        return 'ok, updated email to {0}'.format(email)

    def update_notification_list(self):
        notificationlist = request.args.get('list', type=str)
        poke_list = []
        for item in notificationlist.split(','):
            poke_list.append(item.trim())
        return 'ok, updated list to {0}'.format(poke_list)

    def get_config(self):
        return jsonify(config)

class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                if obj.utcoffset() is not None:
                    obj = obj - obj.utcoffset()
                millis = int(
                    calendar.timegm(obj.timetuple()) * 1000 +
                    obj.microsecond / 1000
                )
                return millis
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
