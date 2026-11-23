/*
 * agents.js — 会議の 3 つの役割 (企画 / プランナー / アプリケーションエンジニア) の能力
 *
 * 言語モデルではありません。議題のキーワードから分野を判定し、分野ごとの知識表
 * (機能・工数・構成・リスク) を使って、決まった手順で発言を組み立てます。
 * 各エージェントは議事録 (それまでの発言の列) だけを見て次の発言を決めるので、
 * 別々のコンピュータで動いていても同じ会議が成り立ちます。
 */
(function (global) {
  "use strict";
  var ROLES = { kikaku: "企画", planner: "プランナー", engineer: "アプリケーションエンジニア" };

  // 機能: [名前, 優先度 (1 が最重要), 実装工数 (人週), データ, 使う技術]
  var DOMAINS = [
    { key: /チャット|メッセージ|会話|sns|コミュニティ|会議/i, name: "メッセージング", target: "離れた場所にいる仲間と素早くやり取りしたい人", value: "必要な相手に、必要な話題だけを確実に届ける",
      kpi: "1 日あたりの送信数と 7 日後の継続率",
      features: [["アカウントとプロフィール", 1, 1.5, "User", "認証"], ["1 対 1 とグループのメッセージ", 1, 3, "Room, Message", "リアルタイム通信"], ["通知", 2, 1.5, "Device", "プッシュ通知"],
                 ["画像とファイルの共有", 3, 2, "Attachment", "オブジェクトストレージ"], ["検索", 3, 1.5, "SearchIndex", "全文検索"], ["既読と入力中の表示", 4, 1, "Receipt", "リアルタイム通信"]],
      risks: [["同時接続が増えると遅延する", "接続数の上限を決めて負荷試験を行う"], ["通知が届かない端末がある", "主要 OS の実機で確認する"]] },
    { key: /ec|ショップ|通販|販売|決済|注文|カート|店舗/i, name: "販売・注文", target: "商品を手軽に探して買いたい人と、それを売りたい店舗", value: "探す・選ぶ・支払うを迷わず終えられる",
      kpi: "購入完了率と客単価",
      features: [["商品一覧と詳細", 1, 2, "Product", "一覧表示"], ["カートと注文", 1, 2.5, "Cart, Order", "トランザクション"], ["決済", 1, 3, "Payment", "決済代行サービス"],
                 ["会員登録と購入履歴", 2, 1.5, "User", "認証"], ["在庫管理", 2, 2, "Stock", "管理画面"], ["レビュー", 4, 1.5, "Review", "投稿"], ["おすすめ表示", 4, 2, "Recommendation", "集計"]],
      risks: [["決済の審査に時間がかかる", "早い段階で決済代行会社に申請する"], ["在庫と注文がずれる", "注文確定時に在庫を引き当てる"]] },
    { key: /予約|スケジュール|カレンダー|シフト|来店|受付/i, name: "予約・日程", target: "予約を受ける事業者と、空きを見てすぐ予約したい利用者", value: "電話なしで空き確認から予約確定まで終わる",
      kpi: "予約完了率と無断キャンセル率",
      features: [["空き枠の表示", 1, 2, "Slot", "カレンダー"], ["予約と取り消し", 1, 2.5, "Reservation", "排他制御"], ["リマインド通知", 2, 1, "Reminder", "プッシュ通知"],
                 ["事業者向け管理画面", 2, 2.5, "Staff, Shop", "管理画面"], ["事前決済", 3, 3, "Payment", "決済代行サービス"], ["口コミ", 4, 1.5, "Review", "投稿"]],
      risks: [["同じ枠に二重予約が入る", "予約確定を排他制御で守る"], ["無断キャンセルが多い", "リマインドと事前決済を検討する"]] },
    { key: /学習|教育|勉強|教材|クイズ|英語|講座|数学/i, name: "学習", target: "すき間時間で学びを続けたい人", value: "今日やることが分かり、続けた分だけ進みが見える",
      kpi: "週あたりの学習日数と単元の修了率",
      features: [["教材の表示", 1, 2, "Lesson", "コンテンツ配信"], ["問題と採点", 1, 2.5, "Question, Answer", "採点"], ["進み具合の記録", 2, 1.5, "Progress", "集計"],
                 ["復習の出題", 3, 2, "ReviewQueue", "間隔反復"], ["学習リマインド", 3, 1, "Reminder", "プッシュ通知"], ["ランキング", 4, 1.5, "Ranking", "集計"]],
      risks: [["教材の用意が開発より遅れる", "教材の形式を先に決めて並行して作る"], ["続かない利用者が多い", "最初の 1 週間の体験を重点的に試す"]] },
    { key: /健康|医療|運動|歩数|食事|睡眠|ヘルス|体調/i, name: "健康記録", target: "日々の体調を手間なく記録して見返したい人", value: "記録が習慣になり、変化に自分で気づける",
      kpi: "記録日数と 30 日後の継続率",
      features: [["記録の入力", 1, 2, "Record", "フォーム"], ["グラフ表示", 1, 2, "Summary", "グラフ"], ["目標とリマインド", 2, 1.5, "Goal", "プッシュ通知"],
                 ["端末のセンサー連携", 3, 2.5, "SensorData", "OS のヘルスケア API"], ["データの書き出し", 3, 1, "Export", "ファイル出力"], ["家族との共有", 4, 2, "Share", "認証"]],
      risks: [["健康情報の取り扱いに法的な配慮が要る", "個人情報の扱いを専門家に確認する"], ["医療行為と誤解される", "診断ではないことを画面に明記する"]] },
    { key: /業務|管理|在庫|勤怠|日報|申請|社内|営業|顧客/i, name: "業務管理", target: "紙や表計算で管理している現場の担当者", value: "入力が 1 回で済み、状況がすぐ分かる",
      kpi: "入力にかかる時間と入力漏れの件数",
      features: [["データの登録と一覧", 1, 2.5, "Entry", "フォーム"], ["権限と承認の流れ", 1, 2.5, "Role, Approval", "認可"], ["検索と絞り込み", 2, 1.5, "SearchIndex", "検索"],
                 ["集計とレポート", 2, 2, "Report", "集計"], ["CSV の取り込みと書き出し", 3, 1.5, "Import", "ファイル入出力"], ["通知", 4, 1, "Notice", "通知"]],
      risks: [["現場の運用と画面が合わない", "早い段階で試作を現場に見せる"], ["既存データの移行に手間がかかる", "移行の手順を先に試す"]] },
    { key: /ゲーム|パズル|対戦|スコア|遊/i, name: "ゲーム", target: "短い時間で気軽に遊びたい人", value: "すぐ始められて、もう 1 回やりたくなる",
      kpi: "1 回あたりのプレイ時間と翌日の継続率",
      features: [["基本の遊び", 1, 4, "Stage", "ゲームループ"], ["スコアと記録", 2, 1, "Score", "保存"], ["ステージ追加", 2, 2.5, "Stage", "データ駆動"],
                 ["ランキング", 3, 1.5, "Ranking", "集計"], ["効果音と演出", 3, 1.5, "Asset", "音声"], ["対戦", 4, 3.5, "Match", "リアルタイム通信"]],
      risks: [["面白さが作ってみるまで分からない", "基本の遊びだけを先に作って試す"], ["端末によって動きが重い", "古い端末で早めに確認する"]] }
  ];
  var GENERIC = { name: "一般", target: "この課題を日常的に抱えている人", value: "今より少ない手間で目的を果たせる", kpi: "週あたりの利用回数と継続率",
    features: [["中心となる機能", 1, 3, "Item", "フォーム"], ["アカウント", 2, 1.5, "User", "認証"], ["一覧と検索", 2, 1.5, "SearchIndex", "検索"],
               ["通知", 3, 1, "Notice", "プッシュ通知"], ["設定", 3, 1, "Setting", "保存"], ["データの書き出し", 4, 1, "Export", "ファイル出力"]],
    risks: [["求められている機能がまだはっきりしない", "利用者 5 人に試作を見せて確かめる"], ["範囲が広がりやすい", "初版の範囲を議事録で固定する"]] };

  function domainOf(text) { for (var i = 0; i < DOMAINS.length; i++) if (DOMAINS[i].key.test(text)) return DOMAINS[i]; return GENERIC; }
  function platformsOf(text) {
    var p = [];
    if (/android|アンドロイド|apk|スマホ|スマートフォン|モバイル|携帯/i.test(text)) p.push("Android");
    if (/ios|iphone|アイフォン|スマホ|スマートフォン|モバイル/i.test(text)) p.push("iOS");
    if (/windows|ウィンドウズ|pc|パソコン|デスクトップ|exe/i.test(text)) p.push("Windows");
    if (/linux|ubuntu|deb/i.test(text)) p.push("Linux");
    if (/web|ブラウザ|サイト/i.test(text) || !p.length) p.push("Web");
    return p;
  }
  // 「3か月」「10週間」などの期限 → 週数。指定が無ければ null
  function deadlineOf(text) {
    var z = String(text).replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xfee0); });
    var m = z.match(/(\d+(?:\.\d+)?)\s*(週間|週|か月|ヶ月|ヵ月|カ月|ケ月|箇月|月間|日間|日)/);
    if (!m) return null;
    var n = +m[1];
    return m[2].indexOf("週") >= 0 ? n : m[2].indexOf("日") >= 0 ? Math.round(n / 7 * 10) / 10 : Math.round(n * 4.33 * 10) / 10;
  }
  var OVERHEAD = { requirements: 0.15, design: 0.15, test: 0.25, release: 0.05 };      // 実装工数に対する比
  function estimate(features, platforms, team) {
    var impl = features.reduce(function (s, f) { return s + f.weeks; }, 0) * (1 + 0.35 * (platforms.length - 1));
    var total = impl * (1 + OVERHEAD.requirements + OVERHEAD.design + OVERHEAD.test + OVERHEAD.release);
    var r1 = function (x) { return Math.round(x * 10) / 10; };
    return { impl: r1(impl), person_weeks: r1(total), team: team, calendar_weeks: r1(total / team),
             phases: [["要件定義", r1(impl * OVERHEAD.requirements / team)], ["設計", r1(impl * OVERHEAD.design / team)], ["実装", r1(impl / team)],
                      ["試験", r1(impl * OVERHEAD.test / team)], ["公開準備", r1(impl * OVERHEAD.release / team)]] };
  }
  function stackOf(platforms) {
    var mobile = platforms.indexOf("Android") >= 0 || platforms.indexOf("iOS") >= 0, desktop = platforms.indexOf("Windows") >= 0 || platforms.indexOf("Linux") >= 0;
    var client = platforms.length > 1 ? "画面は Web 技術 (HTML / JavaScript) で 1 つ作り、" + (mobile ? "モバイルは Cordova、" : "") + (desktop ? "デスクトップは Electron、" : "") + "で包む"
      : platforms[0] === "Web" ? "Web アプリ (HTML / JavaScript)" : platforms[0] + " 向けに Web 技術で作り " + (mobile ? "Cordova" : "Electron") + " で包む";
    return { client: client.replace(/、で包む$/, " で包む"), server: "HTTP API (認証つき) と、必要な箇所だけリアルタイム通信", db: "リレーショナルデータベース" };
  }

  var last = function (msgs, kinds) { for (var i = msgs.length - 1; i >= 0; i--) if (kinds.indexOf(msgs[i].kind) >= 0) return msgs[i]; return null; };
  var names = function (fs) { return fs.map(function (f) { return f.name; }).join("、"); };

  /* ── 各役割: 議事録 msgs を見て、次の発言 {kind, text, data} か null を返す ── */
  var AGENTS = {
    kikaku: function (msgs) {
      var tail = msgs[msgs.length - 1]; if (!tail) return null;
      if (tail.kind === "agenda") {
        var text = tail.text, d = domainOf(text), pf = platformsOf(text), dl = deadlineOf(text);
        var features = d.features.map(function (f) { return { name: f[0], priority: f[1], weeks: f[2], data: f[3], tech: f[4] }; });
        return { kind: "propose", data: { domain: d.name, target: d.target, value: d.value, kpi: d.kpi, features: features, later: [], platforms: pf, deadline_weeks: dl },
          text: "企画です。分野は「" + d.name + "」と見ました。対象は" + d.target + "。提供する価値は「" + d.value + "」です。" +
                "機能は優先度順に、" + names(features) + "を考えています。対応環境は " + pf.join("・") + "、成功の指標は" + d.kpi + "です。" +
                (dl ? "期限は " + dl + " 週間です。" : "期限の指定は無いので、見積りをもとに決めましょう。") + "エンジニアさん、見積りをお願いします。" };
      }
      if (tail.kind === "concern") {
        var p = last(msgs, ["propose", "revise"]).data, over = tail.data.over_weeks, team = tail.data.team;
        var keep = p.features.slice(), later = p.later.slice();
        // 優先度の低い機能から順に次期へ回し、期限に収まるところで止める (優先度 1 は残す)
        while (keep.length && estimate(keep, p.platforms, team).calendar_weeks > p.deadline_weeks) {
          var idx = -1; keep.forEach(function (f, i) { if (f.priority > 1 && (idx < 0 || f.priority >= keep[idx].priority)) idx = i; });
          if (idx < 0) break;
          later.unshift(keep.splice(idx, 1)[0]);
        }
        var moved = later.slice(0, later.length - p.later.length), fits = estimate(keep, p.platforms, team).calendar_weeks <= p.deadline_weeks;
        var data = Object.assign({}, p, { features: keep, later: later });
        if (!moved.length || !fits) {
          data.deadline_weeks = estimate(keep, p.platforms, team).calendar_weeks;
          return { kind: "revise", data: data, text: "企画です。" + (moved.length ? names(moved) + "を次期に回しますが、" : "") + "最重要の機能 (" + names(keep) + ") はこれ以上削れません。" +
            "期限を " + data.deadline_weeks + " 週間に延ばす案でお願いします。エンジニアさん、再見積りをお願いします。" };
        }
        return { kind: "revise", data: data, text: "企画です。" + over + " 週間の超過、了解しました。" + names(moved) + "を次期に回し、初版は" + names(keep) + "に絞ります。エンジニアさん、再見積りをお願いします。" };
      }
      // 日程が出たら合意する。エンジニアの合意が先に届いていても同じ (発言の届く順序に依らない)
      if (tail.kind === "schedule" || (tail.kind === "agree" && tail.role === "engineer")) {
        var sch = last(msgs, ["schedule"]);
        if (sch && !msgs.some(function (m) { return m.kind === "agree" && m.role === "kikaku" && m.seq > sch.seq; }))
          return { kind: "agree", data: {}, text: "企画です。この計画で提供する価値は保てます。合意します。" };
      }
      return null;
    },
    engineer: function (msgs) {
      var tail = msgs[msgs.length - 1]; if (!tail) return null;
      if (tail.kind === "propose" || tail.kind === "revise") {
        var p = tail.data, team = 2, e = estimate(p.features, p.platforms, team), st = stackOf(p.platforms);
        var entities = []; p.features.forEach(function (f) { f.data.split(/,\s*/).forEach(function (x) { if (entities.indexOf(x) < 0) entities.push(x); }); });
        return { kind: "estimate", data: { estimate: e, stack: st, entities: entities, team: team },
          text: "エンジニアです。構成は、" + st.client + "。サーバーは " + st.server + "、保存は" + st.db + "です。主なデータは " + entities.join("、") + "。" +
                "工数は機能ごとに " + p.features.map(function (f) { return f.name + " " + f.weeks + " 人週"; }).join("、") + "。" +
                (p.platforms.length > 1 ? "対応環境が " + p.platforms.length + " つあるので実装を " + Math.round(35 * (p.platforms.length - 1)) + "% 上乗せし、" : "") +
                "要件定義・設計・試験・公開準備を含めて合計 " + e.person_weeks + " 人週、" + team + " 人で " + e.calendar_weeks + " 週間です。プランナーさん、日程をお願いします。" };
      }
      if (tail.kind === "schedule" || (tail.kind === "agree" && tail.role === "kikaku")) {
        var s = last(msgs, ["schedule"]);
        if (s && !msgs.some(function (m) { return m.kind === "agree" && m.role === "engineer" && m.seq > s.seq; }))
          return { kind: "agree", data: {}, text: "エンジニアです。この日程で実装できます。試験は、機能ごとの自動テストと、公開前の実機確認で進めます。合意します。" };
      }
      return null;
    },
    planner: function (msgs) {
      var tail = msgs[msgs.length - 1]; if (!tail) return null;
      if (tail.kind === "estimate") {
        var p = last(msgs, ["propose", "revise"]).data, e = tail.data.estimate, dl = p.deadline_weeks;
        if (dl !== null && e.calendar_weeks > dl) {
          var over = Math.round((e.calendar_weeks - dl) * 10) / 10;
          return { kind: "concern", data: { over_weeks: over, team: e.team },
            text: "プランナーです。見積りは " + e.calendar_weeks + " 週間で、期限の " + dl + " 週間を " + over + " 週間超えます。企画さん、初版の範囲を絞るか、期限の見直しをお願いします。" };
        }
        var d = domainOf(msgs[0].text), acc = 0, sum = e.phases.reduce(function (t, ph) { return t + ph[1]; }, 0) || 1;
        // 各工程の終わりは、丸める前の比率から積み上げる (合計が見積りの週数と必ず一致する)
        var milestones = e.phases.map(function (ph, i) {
          acc += ph[1];
          return { phase: ph[0], weeks: ph[1], end_week: i === e.phases.length - 1 ? e.calendar_weeks : Math.round(acc / sum * e.calendar_weeks * 10) / 10 };
        });
        var week = e.calendar_weeks;
        return { kind: "schedule", data: { milestones: milestones, total_weeks: week, deadline_weeks: dl, risks: d.risks, team: e.team },
          text: "プランナーです。日程を組みました。" + milestones.map(function (m) { return m.phase + " " + m.weeks + " 週間 (第 " + m.end_week + " 週まで)"; }).join("、") + "。全体で " + week + " 週間" +
                (dl !== null ? "、期限 " + dl + " 週間に対して余裕は " + Math.round((dl - week) * 10) / 10 + " 週間です。" : "です。これを期限とします。") +
                "リスクは、" + d.risks.map(function (r) { return r[0] + " → " + r[1]; }).join("。") + "。企画さん、エンジニアさん、合意できますか。" };
      }
      if (tail.kind === "agree") {
        var s = last(msgs, ["schedule"]); if (!s) return null;
        var after = msgs.filter(function (m) { return m.kind === "agree" && m.seq > s.seq; }).map(function (m) { return m.role; });
        if (after.indexOf("kikaku") >= 0 && after.indexOf("engineer") >= 0 && !msgs.some(function (m) { return m.kind === "decide"; })) {
          var pp = last(msgs, ["propose", "revise"]).data;
          return { kind: "decide", data: {}, text: "プランナーです。全員の合意が取れました。決定事項: 初版は" + names(pp.features) + "。" +
            (pp.later.length ? "次期に回すのは" + names(pp.later) + "。" : "") + "期間は " + s.data.total_weeks + " 週間、体制は " + s.data.team + " 人です。以上で会議を終わります。" };
        }
      }
      return null;
    }
  };

  // 人の発言 (comment) に含まれる指示: 「期限を 8 週間に」→ 議題を更新して会議をやり直す
  function directive(text) {
    var dl = /(期限|締切|締め切り|納期)/.test(text) ? deadlineOf(text) : null;
    return dl ? { deadline_weeks: dl } : null;
  }

  global.BadaAgents = { ROLES: ROLES, AGENTS: AGENTS, domainOf: domainOf, platformsOf: platformsOf, deadlineOf: deadlineOf, estimate: estimate, stackOf: stackOf, directive: directive };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaAgents;
})(typeof window !== "undefined" ? window : globalThis);
