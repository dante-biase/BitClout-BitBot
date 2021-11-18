import math
import os
import re
from datetime import datetime

import rapidjson
import undetected_chromedriver as uc
from munch import Munch as Bunch

import config
import utils

uc.install(target_version=89)

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class AddressBook:
    API_HOME = "https://api.bitclout.com/api/v1"
    EXPLORER_HOME = "https://explorer.bitclout.com/"


class TransactionTypes:
    CREATOR_COIN = "CREATOR_COIN"
    BASIC_TRANSFER = "BASIC_TRANSFER"
    LIKE = "LIKE"
    FOLLOW = "FOLLOW"
    PRIVATE_MESSAGE = "PRIVATE_MESSAGE"
    SUBMIT_POST = "SUBMIT_POST"
    BLOCK_REWARD = "BLOCK_REWARD"

class Converter:

    @staticmethod
    def nanos_to_creator_coins(nanos, bitclout_per_coin):
        total_bitclout = nanos * math.pow(10, -9)
        return total_bitclout / bitclout_per_coin

    @staticmethod
    def nanos_to_usd(nanos, usd_per_bitclout):
        total_bitclout = nanos * math.pow(10, -9)
        return total_bitclout * usd_per_bitclout


class BitClout:

    def __init__(self):
        options = Options()
        args = ["headless", "no-sandbox", "disable-dev-shm-usage"]  # , "./resources/chrome-csp-disable-master.crx"]
        if utils.running_on_windows():
            args += ["log-level=3", "disable-gpu"]

        for arg in args:
            options.add_argument(f"--{arg}")

        # desired_capabilities = DesiredCapabilities.CHROME
        # desired_capabilities['loggingPrefs'] = {'browser':'ALL'}

        self._driver = Chrome(options=options)  # , desired_capabilities=desired_capabilities)
        self._driver.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})

    def check_latest_block_number(self):
        try:
            self._driver.get(f"{AddressBook.EXPLORER_HOME}?query-node=https:%2F%2Fapi.bitclout.com&block-height=-1")
            WebDriverWait(self._driver, 10).until(EC.alert_is_present())
            alert = self._driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            if latest_block_number := re.match('.*?([0-9]+)$', alert_text):
                return int(latest_block_number.group(1))
            else:
                return -1

        except TimeoutException:
            return -1

    # def get_block(self, block_number):
    #     self._driver.get(f"{AddressBook.EXPLORER_HOME}?query-node=https:%2F%2Fapi.bitclout.com&block-height={block_number}")

    def get_latest_block(self):
        self._driver.get(AddressBook.API_HOME)
        block_str = self._driver.find_element_by_tag_name('body').text

        if config.CREATOR_KEY in block_str:
            self._save_as_test_block(block_str)
            # exit(0)

        return self._load_block(block_str)

    def get_test_block(self):
        with open("./resources/test_block.json", 'r', encoding="utf-8") as f:
            block_str = re.sub('\s', '', f.read())

        return self._load_block(block_str)

    def _load_block(self, block_str):
        block_info_str, block_transactions_str = block_str.split(",\"Transactions\":", 1)
        block_info = rapidjson.loads(block_info_str + '}')

        block = Bunch(
            timestamp=datetime.fromtimestamp(block_info["Header"]["TstampSecs"]),
            number=int(block_info["Header"]["Height"]),
            hash=block_info["Header"]["BlockHashHex"],
            transactions=rapidjson.loads("{\"Transactions\": " + block_transactions_str)["Transactions"]
        )
        block.total_transactions = sum(1 for _ in block.transactions)

        return block

    def _save_as_test_block(self, block_str):
        json = rapidjson.loads(block_str)
        with open("./resources/test_block.json", "w+") as f:
            f.write(rapidjson.dumps(json, indent=4, write_mode=rapidjson.WM_PRETTY))

    def filter_block_transactions(self, block, types=None, affected_users=None):
        for txn_data in block.transactions:
            if affected_users[0] in str(txn_data):
                yield txn_data

            # type_ok = True # not types or txn_data["TransactionType"] in types
            # user_related = not affected_users or bool(
            #     (
            #         utils.dict_has_path(txn_data, ["Outputs", 0, "PublicKeyBase58Check"])
            #         and txn_data["Outputs"][0]["PublicKeyBase58Check"] in affected_users
            #     )
            #     or (
            #         utils.dict_has_path(txn_data, ["TransactionMetadata", "AffectedPublicKeys"])
            #         and all(
            #             user_key in [dict_["PublicKeyBase58Check"] for dict_ in txn_data["TransactionMetadata"]["AffectedPublicKeys"]]
            #             for user_key in affected_users
            #         )
            #     )
            # )

            # if type_ok and user_related:
            #     yield txn_data
