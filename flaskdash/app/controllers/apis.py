# Copyright 2018 Twin Tech Labs. All rights reserved

from flask import Blueprint
from flask import request, url_for, flash, send_from_directory, jsonify, render_template_string
from flask_user import current_user, login_required, roles_accepted

from app import db
from app.models.user_models import UserProfileForm
import uuid, json, os
import datetime

from alpha_vantage.timeseries import TimeSeries
from app.tradingapp import lib
from app.tradingapp import strat_macrossover

lib.init()
ts = TimeSeries(key = lib.api_key, output_format = 'pandas')

# When using a Flask app factory we must use a blueprint to avoid needing 'app' for '@app.route'
api_blueprint = Blueprint('api', __name__, template_folder='templates')

@api_blueprint.route('/example', methods=['POST'])
def sample_page():

    ret = {"sample return": 10}
    return(jsonify(ret), 200)

@api_blueprint.route('/quote_data', methods=['GET'])
def quote_data():
    report_dict = {}

    col_dict = {
        '1. open': 'Open',
        '2. high': 'High',
        '3. low': 'Low',
        '4. close': 'Close',
        '5. volume': 'Volume'
    }
    #if
    interval = '1min'
    ticker = 'GOOG'
    df, metadata = ts.get_intraday(ticker, interval='60min', outputsize='full')
    df.rename(columns=col_dict, inplace=True)  # Rename column of data

    #json_data = [{'data': list(value.values), 'name': key} for key, value in df.items()]
    df.reset_index(inplace=True)

    result = df.to_json(orient='values', date_unit='ms')
    #featureList = col_dict.values()
    #for feature in featureList:
    print(df)
    print(result)

    return result
