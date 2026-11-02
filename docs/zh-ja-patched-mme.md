# Chinese-patched MMD: MME compatibility / 中文补丁兼容 / 中国語パッチ互換

[中文](#中文) · [日本語](#日本語) · [English](#english)

适配其他版本 / 別ビルドへの対応 / Adapting other builds: [workflow](adapting-mmd-builds.md).

## 中文

### 范围与改动

`compat/zh-ja-patched-mme` 是面向中日文混合界面及 CP936 Windows 的独立兼容分支。
本次 PR 以此分支为目标，保留上游 `main` 的现有支持范围。
适配以已观察到的控件及文字为依据，不能据此推断所有中文补丁或修改版 EXE 都兼容。

- 接受模式按钮的精确别名 `相機編`、`模型編`，保留已有日文和英文标签。
- 接受中文 Windows 文件窗口的 `打开`、`另存为` 标题及 `打开(&O)` 按钮。
  MMD 界面语言和 Windows 文件窗口语言分别处理。
- 文件提交后，仅忽略已销毁控件产生的 Win32 错误 1400，其他错误继续上报。
- EMM 读写增加显式 `encoding="cp936"`；离线工具默认仍为 `cp932`。
  实机传输在 Windows 活动代码页为 936 时选 CP936，其他情况沿用 CP932，结果返回 `encoding`。
  读取已有文件时可显式指定其实际编码。
- 纯表情批处理通过 UI 调整 MME 控制器，不创建骨骼内存对象。
  目标帧已显示时跳过重新求值，保留尚未注册的调整；跨帧操作仍会求值。

### 使用与验证

按 README 安装 Python 环境，自行准备并打开 MMD 和 MME。
本适配不提供 MMD、DLL 二进制、模型、贴图或效果预设。
已连接 MCP 的客户端可直接调用工具；也可在仓库根目录运行可选脚本：

```powershell
.\.venv\Scripts\python.exe scripts/call_mmd.py list-tools
.\.venv\Scripts\python.exe scripts/call_mmd.py mmd_list_windows
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

参数以 UTF-8 JSON 对象保存，用 `--arguments arguments.json` 传入。
遵循工具 schema；文件操作通常要求绝对路径。每次重新取得窗口句柄。
调用脚本仅启动 Python MCP 服务，连接现有 MMD。

1. 读取 `mmd_get_ui_state` 和 `mmd_get_scene_settings`。
2. 用 `mmd_transfer_effect_assignments` 导出新的 EMM，保留返回的 `encoding`。
3. 将同一编码传给 `mmd_read_effect_assignments` 和 `mmd_write_effect_assignments`，另写新副本。
4. 导入副本，再次导出，比对对象、效果分区、材质分配和可见性。

EMM 对象 ID 不等于 UI 模型序号；Ray 分区须先加载对应效果。
先读取控制器真实表情名，试调使用 `register_key=false`，需要保留到动画时再注册。

自动化测试使用合成数据和模拟控件，不依赖私人素材。
曾在已打开的混合界面 MMD 中验证 EMM 导出、CP936 读写、导入、再次导出比对、同帧纯表情调整和截图。
运行记录含场景路径与画面，应保留在本地。
可选的 `scripts/smoke_current_mme.py --apply --hwnd $MmdHwnd` 会导出并重新导入相同分配。
先保存工程，仅在明确选定的测试场景中执行；`$MmdHwnd` 是刚查询到的窗口句柄。
`--morph-model-index` 可额外验证指定模型的当前表情值重设，不注册关键帧。

### 限制

骨骼内存布局、原版 EXE 哈希校验和原生选择桥保持原样；修改版 EXE 的骨骼枚举、选择和变换未获新增支持。
删除确认、清空场景、工程替换及全部输出窗口尚未全面验证。接口成功后仍应检查实际渲染效果。

## 日本語

### 対象と変更内容

`compat/zh-ja-patched-mme` は、日中混在 UI と CP936 Windows 向けの独立した互換ブランチです。
この PR のマージ先は同ブランチであり、上流 `main` の対応範囲は維持します。
観測したコントロールと文字列を対象とし、すべての中国語パッチや改変 EXE の互換性を保証しません。

- モードボタンの完全一致別名 `相機編`、`模型編` を追加し、既存の日本語・英語を維持します。
- 中国語 Windows の `打开`、`另存为` と `打开(&O)` を受け付けます。
  MMD の言語と Windows ファイルダイアログの言語は別々に扱います。
- ファイル送信後に破棄されたコントロールの Win32 エラー 1400 のみを無視し、他のエラーは報告します。
- EMM の読み書きに明示的な `encoding="cp936"` を追加します。オフラインの既定値は `cp932` です。
  実機転送では Windows のアクティブコードページが 936 の場合に CP936、それ以外は CP932 を選び、
  結果に `encoding` を返します。既存ファイルの実際の文字コードも明示できます。
- モーフのみのバッチは UI を使い、ボーンメモリを開きません。
  現在フレームの再評価を省略して未登録の調整を維持します。別フレームへの移動では再評価が行われます。

### 利用と検証

README に従って Python 環境を用意し、利用者自身で MMD と MME を起動してください。
MMD、DLL バイナリ、モデル、テクスチャ、エフェクトのプリセットは同梱しません。
接続済み MCP クライアントから直接呼ぶか、リポジトリのルートで任意の補助スクリプトを使います。

```powershell
.\.venv\Scripts\python.exe scripts/call_mmd.py list-tools
.\.venv\Scripts\python.exe scripts/call_mmd.py mmd_list_windows
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

引数は UTF-8 JSON オブジェクトをファイルに保存し、`--arguments arguments.json` で渡します。
ツールの schema に従ってください。ファイル操作では通常、絶対パスが必要です。ハンドルは毎回取得します。
補助スクリプトは Python MCP サーバーのみを起動し、既存の MMD に接続します。

1. `mmd_get_ui_state` と `mmd_get_scene_settings` を読みます。
2. `mmd_transfer_effect_assignments` で新規 EMM にエクスポートし、返された `encoding` を保持します。
3. 同じ文字コードで `mmd_read_effect_assignments` と `mmd_write_effect_assignments` を使い、別ファイルを作ります。
4. インポート後に再エクスポートし、オブジェクト、描画対象、材質割当、可視性を比較します。

EMM のオブジェクト ID は UI のモデル番号とは異なります。Ray の描画対象は対応エフェクトの読み込み後に現れます。
実際のモーフ名を確認し、試行には `register_key=false` を使います。アニメーションに残す場合はキーを登録します。

自動テストは合成データとモックを使い、個人の素材には依存しません。
既存の混在 UI の MMD で EMM 入出力、CP936 読み書き、再エクスポート比較、同一フレームのモーフ調整とキャプチャを検証しました。
実行記録にはシーンのパスや画像が含まれるため、手元に保持してください。
任意の `scripts/smoke_current_mme.py --apply --hwnd $MmdHwnd` は同じ割当をエクスポートして再インポートします。
先にプロジェクトを保存し、明示的に選んだテスト用シーンでのみ実行します。`$MmdHwnd` は直前に取得したハンドルです。
`--morph-model-index` は指定モデルの現在のモーフ値をキー登録なしで再設定します。

### 制限

ボーンメモリのレイアウト、既存 EXE のハッシュ制限、ネイティブ選択ブリッジは変更しません。
改変 EXE のボーン列挙・選択・変換は追加対応の対象外です。
削除確認、シーン初期化、プロジェクト置換、すべての出力ダイアログは通し検証していません。
ツールの成功結果に加えて、実際の描画を目視確認してください。

## English

### Scope and changes

`compat/zh-ja-patched-mme` is a separate compatibility branch for mixed Japanese/Chinese UI labels
and CP936 Windows. This PR targets that branch, preserving upstream `main`'s support scope.
Compatibility is based on observed controls and exact labels; it does not establish support for
every Chinese patch or modified executable.

- Accept exact mode-button aliases `相機編` and `模型編`, retaining existing Japanese and English labels.
- Accept Chinese Windows file-dialog titles `打开`, `另存为`, and the `打开(&O)` button.
  MMD's editing language and the Windows common-dialog language are handled independently.
- Ignore Win32 error 1400 only for a control already destroyed after file submission; still raise other errors.
- Add explicit `encoding="cp936"` to EMM read/write tools, keeping the offline default `cp932`.
  Live transfers select CP936 when the Windows active code page is 936 and otherwise retain CP932;
  the result includes `encoding`. An existing file's actual encoding can be specified explicitly.
- Run morph-only controller batches through UI controls without opening bone memory.
  Skip re-evaluation if the target frame is already displayed to preserve unregistered edits.
  Moving to another frame still evaluates the animation.

### Usage and verification

Install the Python environment following the README, and start your own MMD with MME.
No MMD executable, DLL binary, models, textures, or effect presets are included.
Use a connected MCP client directly, or run the optional helper from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/call_mmd.py list-tools
.\.venv\Scripts\python.exe scripts/call_mmd.py mmd_list_windows
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Save arguments as a UTF-8 JSON object and pass `--arguments arguments.json`.
Follow each tool's schema; file operations generally require absolute paths. Acquire fresh window handles.
The helper starts only the Python MCP server and connects to an existing MMD instance.

1. Read `mmd_get_ui_state` and `mmd_get_scene_settings`.
2. Export a new EMM with `mmd_transfer_effect_assignments`, retaining its returned `encoding`.
3. Pass that encoding to `mmd_read_effect_assignments` and `mmd_write_effect_assignments`, writing a separate copy.
4. Import the copy, export again, and compare objects, render targets, material assignments, and visibility.

EMM object IDs are not UI model indices. Ray render targets appear after the corresponding effects are loaded.
Read actual controller morph names first; use `register_key=false` for trial adjustments and register keys
when the values should persist in the animation.

Automated regressions use synthetic data and mocked controls, without private assets.
An existing mixed-UI MMD instance was used to verify EMM transfers, CP936 read/write, re-export comparison,
same-frame morph adjustment, and capture. Runtime reports contain scene paths and images and should remain local.
The optional `scripts/smoke_current_mme.py --apply --hwnd $MmdHwnd` exports and reimports identical assignments.
Save the project first and run it only on an explicitly selected test scene; `$MmdHwnd` is a freshly queried handle.
Optionally pass `--morph-model-index` to reapply one displayed morph value on that model without registering keys.

### Limitations

Bone memory layouts, the existing executable hash restriction, and the native selection bridge remain unchanged.
Bone enumeration, selection, and transforms on modified executables are not newly supported.
Deletion confirmations, scene clearing, project replacement, and every output dialog have not been validated end to end.
Inspect the actual rendering in addition to tool success responses.
