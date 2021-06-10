from sql_metadata import Parser
from sql_metadata.keywords_lists import QueryType


def test_with_statements():
    parser = Parser(
        """
WITH
database1.tableFromWith AS (SELECT aa.* FROM table3 as aa 
                            left join table4 on aa.col1=table4.col2),
test as (SELECT * from table3)
SELECT
"xxxxx"
FROM
database1.tableFromWith alias
LEFT JOIN database2.table2 ON ("tt"."ttt"."fff" = "xx"."xxx")
"""
    )
    assert parser.tables == ["table3", "table4", "database2.table2"]

    assert parser.with_names == ["database1.tableFromWith", "test"]

    parser = Parser(
        """
WITH
database1.tableFromWith AS (SELECT * FROM table3),
database1.tableFromWith2 AS (SELECT * FROM table4),
database1.tableFromWith3 AS (SELECT * FROM table5),
database1.tableFromWith4 AS (SELECT * FROM table6)
SELECT
"xxxxx"
FROM
database1.tableFromWith alias
LEFT JOIN database2.table2 ON ("tt"."ttt"."fff" = "xx"."xxx")
"""
    )

    assert parser.with_names == [
        "database1.tableFromWith",
        "database1.tableFromWith2",
        "database1.tableFromWith3",
        "database1.tableFromWith4",
    ]

    assert parser.tables == ["table3", "table4", "table5", "table6", "database2.table2"]

    parser = Parser(
        """
WITH
cte1 AS (SELECT a, b FROM table1),
cte2 AS (SELECT c, d FROM table2)
SELECT b, d FROM cte1 JOIN cte2
WHERE cte1.a = cte2.c;
"""
    )

    assert parser.with_names == ["cte1", "cte2"]

    assert parser.tables == ["table1", "table2"]


def test_with_with_columns():
    # fix for setting columns in with
    # https://github.com/macbre/sql-metadata/issues/128
    query = (
        "WITH t1 AS (SELECT * FROM t2), "
        "t3 (c1, c2) AS (SELECT c3, c4 FROM t4) SELECT * FROM t1, t3, t5;"
    )
    parser = Parser(query)
    assert parser.with_names == ["t1", "t3"]
    assert parser.tables == ["t2", "t4", "t5"]
    assert parser.columns == ["*", "c3", "c4"]
    assert parser.columns_aliases_names == ["c1", "c2"]
    assert parser.columns_aliases == {"c1": "c3", "c2": "c4"}


def test_multiple_with_statements_with_with_columns():
    # fix for setting columns in with
    # https://github.com/macbre/sql-metadata/issues/128
    query = """
    WITH 
    t1 (c1, c2) AS (SELECT * FROM t2),
    t3 (c3, c4) AS (SELECT c5, c6 FROM t4) 
    SELECT * FROM t1, t3;
    """
    parser = Parser(query)
    assert parser.with_names == ["t1", "t3"]
    assert parser.tables == ["t2", "t4"]
    assert parser.columns == ["*", "c5", "c6"]
    assert parser.columns_aliases_names == ["c1", "c2", "c3", "c4"]
    assert parser.columns_aliases == {"c1": "*", "c2": "*", "c3": "c5", "c4": "c6"}
    assert parser.query_type == QueryType.SELECT


def test_complicated_with():
    query = """
    WITH uisd_filter_table as (
        select
            session_id,
            srch_id,
            srch_ci,
            srch_co,
            srch_los,
            srch_sort_type,
            impr_list
        from
            uisd
        where
            datem <= date_sub(date_add(current_date(), 92), 7 * 52)
            and lower(srch_sort_type) in ('expertpicks', 'recommended')
            and srch_ci <= date_sub(date_add(current_date(), 92), 7 * 52)
            and srch_co >= date_sub(date_add(current_date(), 1), 7 * 52)
    )
    select
        DISTINCT session_id,
        srch_id,
        srch_ci,
        srch_co,
        srch_los,
        srch_sort_type,
        l.impr_property_id as expe_property_id,
        l.impr_position_across_pages
    from
        uisd_filter_table lateral view explode(impr_list) table as l
    """
    parser = Parser(query)
    assert parser.query_type == QueryType.SELECT
    assert parser.with_names == ["uisd_filter_table"]
    assert parser.tables == [
        "uisd",
        "impr_list",
    ]  # this one is wrong too should be table
    assert parser.columns == [
        "session_id",
        "srch_id",
        "srch_ci",
        "srch_co",
        "srch_los",
        "srch_sort_type",
        "impr_list",
        "datem",
        "l.impr_property_id",
        "l.impr_position_across_pages",
    ]