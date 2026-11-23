/*
 * meeting.js — 会議の状態: 議事録・エントロピーによる計測・エージェントの順番・書き出し
 * (DOM にも通信にも依存しない。どのコンピュータでも同じ議事録から同じ結果になる)
 */
(function (global) {
  "use strict";
  var req = function (g, f) { return global[g] || (typeof require !== "undefined" ? require(f) : null); };
  var En = req("BadaEntropy", "./entropy.js"), Ag = req("BadaAgents", "./agents.js");
  var ORDER = ["kikaku", "engineer", "planner"];

  function Meeting() { this.msgs = []; this.context = En.bag(""); this.fs = []; }
  // 番号つきの発言を議事録に加える。議題からのずれ D と門 (E2) の結果を付ける
  Meeting.prototype.add = function (m) {
    if (m.kind === "agenda") { this.msgs = []; this.fs = []; this.context = En.bag(m.text); }      // 新しい議題は議事録を始め直す
    else if (this.msgs.some(function (x) { return x.seq === m.seq; })) return null;
    var rec = Object.assign({}, m);
    rec.measure = m.kind === "agenda" ? En.measure(m.text, En.bag(m.text)) : En.measure(m.text, this.context);
    this.msgs.push(rec); this.msgs.sort(function (a, b) { return a.seq - b.seq; });
    if (m.kind !== "agenda") { this.fs.push(rec.measure.D); if (rec.measure.pass) this.context = En.merge([this.context, En.bag(m.text)]); }
    return rec;
  };
  // 役割 role のエージェントの次の発言 (無ければ null)。人の発言 (comment) は飛ばして考える
  Meeting.prototype.next = function (role) {
    var flow = this.msgs.filter(function (m) { return m.kind !== "comment"; });
    return Ag.AGENTS[role] ? Ag.AGENTS[role](flow) : null;
  };
  Meeting.prototype.decided = function () { return this.msgs.some(function (m) { return m.kind === "decide"; }); };
  Meeting.prototype.stats = function () {
    var body = this.msgs.filter(function (m) { return m.kind !== "agenda"; });
    var all = En.merge(body.map(function (m) { return En.bag(m.text); }));
    return { count: body.length, H: En.entropy(all), flow: En.flow(this.fs), off_topic: body.filter(function (m) { return !m.measure.pass; }).length,
             mean_D: body.length ? this.fs.reduce(function (a, b) { return a + b; }, 0) / body.length : 0 };
  };
  var find = function (msgs, kinds) { for (var i = msgs.length - 1; i >= 0; i--) if (kinds.indexOf(msgs[i].kind) >= 0) return msgs[i]; return null; };
  // 決定事項を企画書・計画・設計にまとめる (Markdown)
  Meeting.prototype.minutes = function () {
    var ms = this.msgs, ag = ms[0], p = find(ms, ["propose", "revise"]), e = find(ms, ["estimate"]), s = find(ms, ["schedule"]), st = this.stats();
    var out = ["# 会議の議事録と計画書", "", "**議題**: " + (ag ? ag.text : "(なし)"), "", "**状態**: " + (this.decided() ? "決定済み" : "進行中 (未決定)"), ""];
    if (p) out = out.concat(["## 1. 企画", "", "- 分野: " + p.data.domain, "- 対象: " + p.data.target, "- 提供する価値: " + p.data.value, "- 成功の指標: " + p.data.kpi, "- 対応環境: " + p.data.platforms.join("・"), "",
      "| 初版の機能 | 優先度 | 実装工数 (人週) |", "|:--|:--|:--|"].concat(p.data.features.map(function (f) { return "| " + f.name + " | " + f.priority + " | " + f.weeks + " |"; }),
      p.data.later.length ? ["", "次期に回す機能: " + p.data.later.map(function (f) { return f.name; }).join("、")] : [], [""]));
    if (e) out = out.concat(["## 2. 設計と見積り", "", "- クライアント: " + e.data.stack.client, "- サーバー: " + e.data.stack.server, "- 保存: " + e.data.stack.db, "- 主なデータ: " + e.data.entities.join("、"),
      "- 合計 " + e.data.estimate.person_weeks + " 人週 / " + e.data.team + " 人で " + e.data.estimate.calendar_weeks + " 週間", ""]);
    if (s) out = out.concat(["## 3. 日程", "", "| 工程 | 期間 (週) | 終了 (第 n 週) |", "|:--|:--|:--|"].concat(s.data.milestones.map(function (m) { return "| " + m.phase + " | " + m.weeks + " | " + m.end_week + " |"; }),
      ["", "## 4. リスクと対策", ""], s.data.risks.map(function (r) { return "- " + r[0] + " → " + r[1]; }), [""]));
    out = out.concat(["## 5. 発言の記録", ""], ms.map(function (m) {
      return "- **" + (Ag.ROLES[m.role] || m.name || "参加者") + "** (" + m.kind + (m.kind !== "agenda" && !m.measure.pass ? "・議題から外れている可能性" : "") + "): " + m.text;
    }), ["", "## 6. 会議の計測 (エントロピー)", "", "- 発言数 " + st.count + " / 全体の情報量 H = " + st.H.toFixed(3) + " nat", "- 議題とのずれの平均 D = " + st.mean_D.toFixed(3) + " / 流れ F = " + st.flow.toFixed(4) + " / 門を通らなかった発言 " + st.off_topic + " 件",
      "", "_見積りと日程は、分野ごとの知識表と決まった計算式によるものです。実際の計画では、担当者による確認が必要です。_"]);
    return out.join("\n");
  };

  // 1 台だけで会議を最後まで進める (テストと「自動で進める」用)
  function runLocal(agenda, limit) {
    var mt = new Meeting(), seq = 0, i, spoke;
    mt.add({ seq: seq++, role: "host", kind: "agenda", text: agenda });
    for (i = 0; i < (limit || 40) && !mt.decided(); i++) {
      spoke = false;
      for (var k = 0; k < ORDER.length; k++) {
        var m = mt.next(ORDER[k]);
        if (m) { mt.add(Object.assign({ seq: seq++, role: ORDER[k] }, m)); spoke = true; break; }
      }
      if (!spoke) break;
    }
    return mt;
  }

  global.BadaMeeting = { Meeting: Meeting, runLocal: runLocal, ORDER: ORDER };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaMeeting;
})(typeof window !== "undefined" ? window : globalThis);
