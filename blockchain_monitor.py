import os
import time
from datetime import datetime

from munch import Munch as Bunch

import utils
from src.bitclout import BitClout, TransactionTypes, Converter
from src.bitclout_pulse import BitCloutPulse
from src.exportal import exportal


class BlockchainMonitor:

    def __init__(self, creator_key):
        self._bitclout_pulse = BitCloutPulse()
        self._bitclout = BitClout()
        self._current_bc_usd_price = -1

        self._creator = Bunch(public_key=creator_key, current_bc_price=-1)
        self._latest_block = Bunch(hash='', number=-1)

    def main_loop(self, checks_per_minute):
        time_padding = (7, ' ')
        pad_time = lambda t: f"{t:.3f}".rjust(*time_padding)
        div = (('-' * (time_padding[0] + 2)) + '+').ljust(79, '-')

        delay = 60 / checks_per_minute
        counter = 1
        while True:
            print(f"\rwaiting for new block... ({counter})", end="")
            if self._bitclout.check_latest_block_number() not in {-1, self._latest_block.number}:
                utils.clear_console()
                print(datetime.now())
                print(f"\rnew block detected; downloading...", end='')

                self._refresh_variables()
                new_block, download_time = utils.time_it(self._bitclout.get_latest_block)()

                print(f"\rlatest block:".ljust(79, ' '))
                print(f"    • timestamp: {new_block.timestamp}")
                print(f"    • number: {new_block.number}")
                print(f"    • hash: {new_block.hash}")
                print(f"    • total-transactions: {new_block.total_transactions}")
                print()

                print(f"\r{pad_time(download_time)}s | downloaded block")

                print("\rparsing transaction(s)...", end='')
                parsed_txns, parse_time = self._parse_block_transactions(new_block)
                print(f"\r{pad_time(parse_time)}s | parsed block: {len(parsed_txns)} relevant transaction(s) found")

                if not parsed_txns:
                    update_time = 0
                else:
                    print("\rupdating discord...", end='')
                    _, update_time = self._update_discord(parsed_txns)
                    print(f"\r{pad_time(update_time)}s | updated discord")

                process_time = download_time + parse_time + update_time
                print(div)
                print(f"{pad_time(process_time)}s | processed block")
                print()
                print(f"\rwaiting for new block...    ", end="")

                self._latest_block = new_block
                counter = 1

            else:
                counter += 1

            time.sleep(delay)

    @utils.time_it
    def _refresh_variables(self):
        self._creator.current_bc_price = self._bitclout_pulse.get_current_cc_bc_price(self._creator.public_key)
        self._current_bc_usd_price = self._bitclout_pulse.get_current_bc_usd_price()

    @utils.time_it
    def _parse_block_transactions(self, block):
        return list(
            self._bitclout.filter_block_transactions(
                block,
                types=[TransactionTypes.CREATOR_COIN],
                affected_users=[self._creator.public_key]
            )
        )

        # parsed_txns = []
        # for txn_data in self._bitclout.filter_block_transactions(
        #         block,
        #         types=[TransactionTypes.CREATOR_COIN],
        #         affected_users=[self._creator.public_key]
        # ):
        #     try:
        #         metadata = txn_data["TransactionMetadata"]
        #         metadata_cc = metadata["CreatorCoinTxindexMetadata"]
        #         operation_type = metadata_cc["OperationType"]
        #         nanos = int(metadata_cc["BitCloutToSellNanos"]) if operation_type == "buy" else int(
        #             metadata_cc["CreatorCoinToSellNanos"])

        #         txn = Bunch(
        #             transactor=Bunch(
        #                 public_key=metadata["TransactorPublicKeyBase58Check"],
        #                 name=self._bitclout_pulse.get_username(metadata["TransactorPublicKeyBase58Check"])
        #             ),
        #             operation_type=operation_type,
        #             creator_coins=Converter.nanos_to_creator_coins(nanos, self._creator.current_bc_price),
        #             usd=Converter.nanos_to_usd(nanos, self._current_bc_usd_price)
        #         )

        #         parsed_txns.append(txn)

        #     except TypeError:
        #         raise TypeError(txn_data["TransactionMetadata"])

        # return parsed_txns

    @utils.time_it
    def _update_discord(self, parsed_txns):
        exportal.pass_to_async(parsed_txns)
        exportal.get_from_async()
