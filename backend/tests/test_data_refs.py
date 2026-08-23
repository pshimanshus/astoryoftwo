import unittest
from app import data_refs


class DataRefsTests(unittest.TestCase):
    def test_winner_bank_loads_list(self):
        bank = data_refs.load_winner_bank()
        self.assertIsInstance(bank, list)
        self.assertGreater(len(bank), 0)
        self.assertIn("caption", bank[0])

    def test_bank_summary_trims_fields(self):
        bank = data_refs.load_winner_bank()
        summ = data_refs.bank_summary(bank, limit=5)
        self.assertEqual(len(summ), 5)
        self.assertEqual(set(summ[0].keys()), {"caption", "slide_count", "comments", "send_proxy"})

    def test_load_contract_imagegen(self):
        text = data_refs.load_contract("imagegen-contract")
        self.assertIn("1080x1350", text)  # known string from the contract

    def test_house_style_ref_paths_returns_list(self):
        self.assertIsInstance(data_refs.house_style_ref_paths(), list)
