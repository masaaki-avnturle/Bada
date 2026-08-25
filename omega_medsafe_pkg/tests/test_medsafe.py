from omega_medsafe import check, format_report, lookup, normalize


def test_lookup_generic_and_brand_name():
    assert lookup("フルニトラゼパム")[0] == "class"
    assert lookup("セレネース")[0] == "class"       # 商品名
    assert lookup("ハロペリドール")[0] == "class"   # 一般名（同クラス）
    assert lookup("セレネース")[1].name == lookup("ハロペリドール")[1].name


def test_manufacturer_suffix_is_not_a_drug():
    kind, note = lookup("アメル")
    assert kind == "brand"
    assert "ジェネリック" in note


def test_unknown_drug_reported():
    r = check(["存在しない薬XYZ"])
    assert "存在しない薬XYZ" in r.unknown
    assert not r.findings


def test_single_drug_has_no_overlap():
    r = check(["アムロジピン"])
    assert r.findings == []


def test_three_cns_depressants_flag_respiratory_depression():
    r = check(["フルニトラゼパム", "エチゾラム", "ブロチゾラム"])
    tags = {f.tag: f for f in r.findings}
    assert "RESPIRATORY_DEPRESSION" in tags
    assert tags["RESPIRATORY_DEPRESSION"].severity == "重大"
    assert tags["RESPIRATORY_DEPRESSION"].count == 3


def test_two_antihypertensives_flag_hypotension():
    r = check(["アムロジピン", "カンデサルタン"])
    assert any(f.tag == "HYPOTENSION" for f in r.findings)


def test_two_antipsychotics_flag_qt():
    r = check(["セレネース", "リスパダール"])
    tags = {f.tag for f in r.findings}
    assert "QT_PROLONGATION" in tags
    assert "EPS_NMS" in tags


def test_full_list_is_critical():
    r = check(["フルニトラゼパム", "エチゾラム", "ブロチゾラム", "アムロジピン",
               "カンデサルタン", "セレネース", "リスパダール"])
    assert r.has_critical
    tags = {f.tag for f in r.findings}
    for expected in ("CNS_DEPRESSION", "RESPIRATORY_DEPRESSION",
                     "HYPOTENSION", "QT_PROLONGATION"):
        assert expected in tags


def test_report_always_directs_to_professional():
    text = format_report(check(["アムロジピン"]))
    assert "薬剤師" in text
    assert "主治医" in text


def test_report_never_emits_dose_or_recipe():
    """このツールは用量・配合を出力しない、という契約の回帰テスト。"""
    text = format_report(check(["フルニトラゼパム", "エチゾラム", "セレネース"]))
    for forbidden in ("mg", "配合比", "レシピ", "合成", "製造"):
        assert forbidden not in text
