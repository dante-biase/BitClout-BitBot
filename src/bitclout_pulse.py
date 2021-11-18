import re

import rapidjson
import requests
from bs4 import BeautifulSoup
from munch import Munch as Bunch


class AddressBook:
    HOME = "https://www.bitcloutpulse.com"
    BLOCKS = f"{HOME}/explorer/blocks"
    TRANSACTIONS = f"{HOME}/explorer/transactions"
    PROFILES = f"{HOME}/profiles"
    API_PROFILES = f"{HOME}/api/profiles"


class BitCloutPulse:

    def __init__(self):
        self.session = requests.Session()

    def get_username(self, public_key):
        match_found, result = self.find(public_key)
        return result["username"] if match_found else ''

    def get_public_key(self, username):
        match_found, result = self.find(username)
        return result["public_key"] if match_found else ''

    def get_current_cc_bc_price(self, creator_key_or_username):
        match_found, result = self.find(creator_key_or_username)
        return float(result["coin_price_bitclout"]) if match_found else -1

    def get_current_bc_usd_price(self):
        price_label = self._get_soup(AddressBook.HOME) \
            .select_one(
            "body > div > div > div > div.mb-3.d-flex.flex-column.flex-xl-row.justify-content-xl-between.align-items-center > div:nth-child(3) > div")
        if price_label and \
                (current_bc_usd_price := re.match("^\$BitClout: ~\$(\d+\.\d+) USD$", price_label.text.strip())):
            return float(current_bc_usd_price.group(1))
        else:
            return -1

    def get_latest_block_info(self):
        latest_block = self._get_soup(AddressBook.BLOCKS) \
            .select_one("body > div > div > div > div.mt-5 > table > tbody > tr:nth-child(1)")
        block_info = latest_block.findChildren('td')

        block_info = Bunch(
            number=int(block_info[0].text),
            hash=block_info[1].text,
            total_transactions=int(block_info[2].text)
        )

        return block_info

    def find(self, public_key_or_username):
        search_results = self.search(public_key_or_username)
        if search_results:
            first_result = search_results[0]
            if public_key_or_username.lower() in {first_result["username"].lower(), first_result["public_key"].lower()}:
                return True, first_result

        return False, None

    def search(self, public_key_or_username):
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = {
            'page_index': 1,
            'page_size': 1,
            'sort_by': [{'id': 'coin_price_BitCloutPulse_nanos', 'desc': True}],
            'filter_by': [{'id': 'is_verified', 'value': None}], 'search': public_key_or_username
        }

        response_text = requests.post(AddressBook.API_PROFILES, headers=headers, data=rapidjson.dumps(data)).text

        try:
            response = rapidjson.loads(response_text)
            return response["results"]
        except rapidjson.JSONDecodeError:
            return None

    def _get_soup(self, url):
        return BeautifulSoup(self.session.get(url).text, "html.parser")

    # def get_block_transactions(self, block, t_types=[]):
    #     return self._get_block_transactions(block, public_key=None, t_types=t_types)

    # def get_block_transactions_for_user(self, block, public_key, t_types=[]):
    #     return self._get_block_transactions(block, public_key=public_key, t_types=t_types)

    # def _get_block_transactions(self, block, public_key, t_types):
    #     t = list(self._get_block_page_transactions(block, t_types))
    #     print(len(t))
    #     # exit(0)
    #     # for block_page_transactions in t:
    #     futures = [self.session.get(f"{AddressBook.transactions}/{transaction.id_}") for transaction in t]
    #     for future in as_completed(futures):
    #         self.i += 1
    #         print(self.i)
    #             # pprint(block_page_transactions)
    #         #     # exit(0)
    #         #     print(future.result())
    #         #     yield 1
    #         #     response = future.result()
    #         #     html = response.text
    #         #     if not public_key or public_key in html:
    #         #         transaction_page = BeautifulSoup(html, "html.parser")
    #         #         transaction_metadata = json.loads(
    #         #             transaction_page.select_one("body > div > div > div > div.mt-5 > div.card.mt-3 > div > pre").text
    #         #         )
    #         #         return transaction_metadata

    # def _get_block_page_transactions(self, block, t_types=[]):
    #     futures = [self.session.get(f"{AddressBook.blocks}/{block.hash}?page={i}") for i in range(math.ceil(block.total_transactions / 27))]
    #     for future in as_completed(futures):
    #         response = future.result()
    #         html = response.text
    #         block_subpage = BeautifulSoup(html, "html.parser")
    #         transaction_table = list(block_subpage.findChildren("tbody")[1].find_all('tr'))

    #         page_transactions = []
    #         for row in transaction_table:
    #             transaction_info = row.findChildren('td')
    #             transaction = Bunch(
    #                 id_ = transaction_info[1].string,
    #                 type_=transaction_info[2].string
    #             )
    #             if not t_types or transaction.type_ in t_types:
    #                 transaction.link = f"{AddressBook.transactions}/{transaction.id_}"
    #                 yield transaction
    #                 # page_transactions.append(transaction)

    #         # yield page_transactions
