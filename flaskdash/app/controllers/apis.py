# Copyright 2018 Twin Tech Labs. All rights reserved

from flask import Blueprint
from flask import request, url_for, flash, send_from_directory, jsonify, render_template_string
from flask_user import current_user, login_required, roles_accepted

from app import db
from app.models.user_models import UserProfileForm
import uuid, json, os
from datetime import datetime

from alpha_vantage.timeseries import TimeSeries
from app.tradingapp import lib

import yfinance as yf
from dateutil.relativedelta import relativedelta

lib.init()
ts = TimeSeries(key = lib.api_key, output_format = 'pandas')

# When using a Flask app factory we must use a blueprint to avoid needing 'app' for '@app.route'
api_blueprint = Blueprint('api', __name__, template_folder='templates')

@api_blueprint.route('/example', methods=['POST'])
def sample_page():

    ret = {"sample return": 10}
    return(jsonify(ret), 200)

@api_blueprint.route('/ts', methods=['GET'])
def tsapi():

    col_dict = {
        '1. open': 'Open',
        '2. high': 'High',
        '3. low': 'Low',
        '4. close': 'Close',
        '5. volume': 'Volume'
    }

    interval = '1min'
    ticker = request.args['ticker']
    df, metadata = ts.get_intraday(symbol=ticker, interval='60min', outputsize='full')
    df.rename(columns=col_dict, inplace=True)  # Rename column of data

    df.reset_index(inplace=True)

    result = df.to_json(orient='values', date_unit='ms')

    return result

@api_blueprint.route('/yf', methods=['GET'])
def yfapi():

    col_dict = {
        '1. open': 'Open',
        '2. high': 'High',
        '3. low': 'Low',
        '4. close': 'Close',
        '5. volume': 'Volume'
    }


    ticker = request.args['ticker']
    start_date = (datetime.now() - relativedelta(days=7)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    df = yf.download(ticker, start=start_date, end=end_date, interval="1m")

    df.rename(columns=col_dict, inplace=True)  # Rename column of data

    df.reset_index(inplace=True)

    return df.to_json(orient='values', date_unit='ms')
