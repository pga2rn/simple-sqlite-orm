from __future__ import annotations

import time
import sqlite3
from datetime import datetime

import pytest

from simple_sqlite3_orm import ORMBase

from tests.sample_db.table import SampleTable
from tests.sample_db._types import Mystr
from tests.conftest import _generate_random_str


class ORMTest(ORMBase[SampleTable]):
    pass


TABLE_NAME = "test_table"

_cur_timestamp = time.time()
mstr = Mystr(_generate_random_str())
entry_for_test = SampleTable(
    unix_timestamp=_cur_timestamp,  # type: ignore
    unix_timestamp_int=int(_cur_timestamp),  # type: ignore
    datetime_iso8601=datetime.fromtimestamp(_cur_timestamp).isoformat(),  # type: ignore
    key_id=1,
    prim_key=mstr,
    prim_key_sha256hash=mstr.sha256hash,
    prim_key_bln=mstr.bool,
    prim_key_magicf=mstr.magicf,
)


class TestORMBase:

    @pytest.fixture(scope="class")
    def setup_connection(self):
        with sqlite3.connect(":memory:") as conn:
            orm_inst = ORMTest(conn, table_name=TABLE_NAME)
            yield orm_inst

    def test_create_table(self, setup_connection: ORMTest):
        setup_connection.orm_create_table(allow_existed=False)
        setup_connection.orm_create_table(
            allow_existed=True, strict=True, without_rowid=True
        )

        with pytest.raises(sqlite3.DatabaseError):
            setup_connection.orm_create_table(allow_existed=False)

    def test_create_index(self, setup_connection: ORMTest):
        setup_connection.orm_create_index(
            index_name="idx_prim_key_sha256hash",
            index_keys=("prim_key_sha256hash",),
            allow_existed=True,
            unique=True,
        )

        with pytest.raises(sqlite3.DatabaseError):
            setup_connection.orm_create_index(
                index_name="idx_prim_key_sha256hash",
                index_keys=("prim_key_sha256hash",),
                allow_existed=False,
            )

    def test_insert_entries(self, setup_connection: ORMTest):
        setup_connection.orm_insert_entries((entry_for_test,))

        with pytest.raises(sqlite3.DatabaseError):
            setup_connection.orm_insert_entry(entry_for_test, or_option="fail")
        setup_connection.orm_insert_entry(entry_for_test, or_option="ignore")
        setup_connection.orm_insert_entry(entry_for_test, or_option="replace")

    def test_select_entries(self, setup_connection: ORMTest):
        select_result = setup_connection.orm_select_entries(
            _distinct=True,
            _order_by=(("key_id", "DESC"),),
            _limit=1,
            prim_key=mstr,
        )
        select_result = list(select_result)

        assert len(select_result) == 1
        assert select_result[0] == entry_for_test

    def test_function_call(self, setup_connection: ORMTest):
        with setup_connection.orm_con as con:
            cur = con.execute(f"SELECT count(*) FROM {TABLE_NAME};")
            res = cur.fetchone()
            assert res[0] == 1

    def test_delete_entries(self, setup_connection: ORMTest):
        assert setup_connection.orm_delete_entries(key_id=entry_for_test.key_id) == 1
