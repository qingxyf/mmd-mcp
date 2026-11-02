# Adapting another MMD build / 适配其他 MMD 版本 / 別の MMD ビルドへの対応

[中文](#中文) · [日本語](#日本語) · [English](#english)

## 中文

本流程供维护者及 agent 为自己的 MMD 发行版建立兼容配置。
当前已实现的中日文混合界面适配见 [兼容指南](zh-ja-patched-mme.md)。
先将目标拆成可独立验证的 UI、文件编码、控制器和原生骨骼功能。

### 1. 记录基线并保护工程

- 从明确的上游提交创建自己的适配分支，记录提交号、Windows/Python 位数、MMD/MME 版本及补丁来源。
- 先保存工程副本，使用已有实例或专门的测试实例。读取工具 schema，再调用工具，重新获取窗口句柄。
- 如需识别 EXE，可在本地对用户提供的 `$MmdExe` 执行 `Get-FileHash -LiteralPath $MmdExe -Algorithm SHA256`。
  哈希用于识别构建；它不能证明内部布局兼容，也不能作为放宽校验的依据。

### 2. 观察真实控件再修改映射

从仓库根目录执行 `python scripts/call_mmd.py mmd_list_windows` 和 `list-tools`。
读取 `mmd_get_ui_state`、`mmd_get_dialogs`，结合截图确认真实模式和窗口。
若现有读取器不支持该版本，使用只读 Win32 控件枚举检查所选进程的窗口标题、类名、控件 ID、文字及父子关系。
诊断输出只保存在本地，避免上传场景标题、文件列表和截图。

- `src/mmd_mcp/ui_language.py`：为已观察到的按钮添加精确别名；在 `english_mode` 中确认实际命名模式。
  中文补丁不一定改变内部名称编码；不要根据按钮语言推断模型或骨骼编码。
- `src/mmd_mcp/ui_state.py`：检查控件 ID 和所在窗口；若确实不同，增加明确的适配配置并测试。
- `src/mmd_mcp/file_operations.py`：单独检查操作系统的打开/保存窗口、文件名输入框、按钮和覆盖确认。
- `scene_lifecycle.py`、`accessory_controls.py`、`edit_actions.py`：只有需要这些操作时才检查对应确认文字；
  未验证的破坏性操作应继续拒绝执行。不要把任意中文窗口、模糊子串或通用“确定”当作已验证的确认。

### 3. 确认文件编码并完成 MME 往返

用 `python -c "import ctypes; print(ctypes.windll.kernel32.GetACP())"` 查看 Windows 活动代码页。
导出一份包含测试中文路径的 EMM，严格解码并核对路径指向的测试文件；不要按界面语言猜编码或忽略解码错误。

`effects.py` 负责读写编码和保留未修改字节，`effects_live.py` 负责实机传输的编码选择，
`server.py` 负责公开参数。新增编码支持须覆盖三处并同步测试。
离线默认 CP932；本兼容分支仅在活动代码页 936 时自动选 CP936，已有文件可以显式指定编码。
其他代码页没有自动获得支持，须重新验证其实际输出。

导出基线 → 同编码读取 → 将同一分配写入新副本 → 导入副本 → 再导出。
核对对象路径、精确分区、Owner、材质子集和可见性，同时确认帧、模型选择和场景设置。
EMM 对象 ID 是临时标识；如果编号发生变化，按对象身份核对，不要套用 UI 模型序号。

### 4. 将控制器 UI 与原生骨骼接口分开验证

MME 控制器常通过表情滑块工作。先读取真实表情名，用 `mmd_batch_bone_keys` 的纯 `morphs` 项试调，
`register_key=false`，目标帧设为当前帧；核对读回值，且不触发无必要的帧求值。
该 UI 路径可以独立于骨骼内存接口适配。

若确实需要骨骼枚举、选择或变换，另行验证 `bone_state.py` 中的编码、布局、指针和步长，
以及 `native/selection_bridge.cpp` 的调用目标、参数约定与 UI 线程行为。
只在一次性测试场景中操作；完成证据充分的迁移和回归测试前，保留原版哈希限制。
**仅替换哈希不能完成原生接口适配。**

### 5. 测试、记录范围并整理 PR

- 添加合成数据回归测试：新标签、未知标签拒绝、文件控件识别、编码往返、错误保留、同帧表情及骨骼保护。
- 用 `python -m unittest discover -s tests -v` 运行全部测试。
- `python scripts/smoke_mcp.py` 检查 MCP 初始化、schema 和离线文件操作；默认还会只读列出 MMD 窗口。
- 按需在已保存的测试工程上执行 `smoke_current_mme.py --apply --hwnd $MmdHwnd`。
  先阅读脚本；它会重新导入分配，可选表情检查会临时切换所选模型。
- `smoke_scene.py`、`smoke_release.py`、`smoke_editing.py` 会启动并编辑测试实例；仅在需要对应范围时使用。
  本分支没有据此声明修改版 EXE 的全部功能均受支持。

在文档中分别列出自动化测试、已执行的实机测试和未验证范围。
提交前检查所有待上传文件、补丁、PR 正文及提交元数据；移除本机路径、用户名、私人邮箱、密钥、
实际角色/素材名称、截图及运行报告。测试使用合成相对路径，运行产物留在已忽略的目录。
按需要使用 GitHub 隐私邮箱。若 PR 要合入独立兼容分支，先确认该分支已存在且自己有权限创建，
再明确设置 PR 的 base；不要误投 `main`。

## 日本語

保守者や agent が別の MMD 配布版へ対応するための手順です。
既存の日中混在 UI への対応範囲は [互換ガイド](zh-ja-patched-mme.md) を参照してください。
UI、ファイルの文字コード、コントローラー、ネイティブのボーン機能を個別に検証します。

### 1. 基準とプロジェクトの保護

上流の明確なコミットから専用ブランチを作り、コミット番号、Windows/Python のビット数、
MMD/MME のバージョン、パッチの出所を記録します。先にプロジェクトのコピーを保存します。
既存または専用のテスト用インスタンスを使い、schema を読んでからツールを呼び、ハンドルを再取得します。
EXE の識別には、利用者の `$MmdExe` に `Get-FileHash -LiteralPath $MmdExe -Algorithm SHA256` を使用できます。
ハッシュは識別情報であり、内部レイアウトの互換性や検査の緩和を正当化しません。

### 2. 実際のコントロールと文字列

ルートで `python scripts/call_mmd.py mmd_list_windows` と `list-tools` を実行し、
`mmd_get_ui_state`、`mmd_get_dialogs` と画像を確認します。未対応なら、対象プロセスに限定した読み取り専用の
Win32 列挙でタイトル、クラス、ID、文字列、親子関係を調べます。診断出力や画像は手元に保持します。

- `ui_language.py`：完全一致の別名を追加し、`english_mode` で実際の名前モードを確認します。
  UI の中国語化からモデル・ボーンの文字コードを推定しません。
- `ui_state.py`：ID と所有ウィンドウを比較し、差がある場合のみ明示的なアダプターとテストを追加します。
- `file_operations.py`：OS 側の開く・保存、ファイル名欄、ボタン、上書き確認を別途調べます。
- `scene_lifecycle.py`、`accessory_controls.py`、`edit_actions.py`：必要な操作の確認文を個別に検証します。
  未検証の破壊的操作は拒否し、部分一致や汎用の確認ボタンで代用しません。

### 3. EMM の文字コードと往復

`python -c "import ctypes; print(ctypes.windll.kernel32.GetACP())"` でアクティブコードページを確認します。
合成した中国語パスを含む EMM を出力し、厳密に復号してテストファイルの存在を確認します。
UI 言語による推定や復号エラーの無視は行いません。
文字コード追加時は `effects.py` の読み書き、`effects_live.py` の転送、`server.py` の schema とテストを更新します。
オフラインの既定値は CP932 で、このブランチはコードページ 936 の場合のみ CP936 を自動選択します。
既存ファイルは明示指定でき、他のコードページは別途検証が必要です。

基準を出力 → 同じ文字コードで読む → 同じ割当を別ファイルへ書く → 入力 → 再出力します。
パス、描画対象、Owner、材質サブセット、可視性、フレーム、モデル選択、シーン設定を比較します。
EMM ID は一時的な識別子で UI のモデル番号とは異なります。変化した場合は対象の同一性で照合します。

### 4. モーフ UI とボーン内部処理

実際のモーフ名を読み、`mmd_batch_bone_keys` の `morphs` のみ、現在フレーム、
`register_key=false` で試します。読戻しを確認し、不要なフレーム再評価を避けます。
この UI 経路はボーンメモリから独立して対応できます。

ボーンの列挙・選択・変換が必要な場合は、`bone_state.py` の文字コード、レイアウト、ポインター、ストライドと、
`native/selection_bridge.cpp` の呼出先・引数規約・UI スレッド動作を別途調べます。
使い捨てのテストシーンのみで検証し、移植と回帰テストが完了するまで元のハッシュ制限を維持します。
**ハッシュの書き換えだけではネイティブ対応になりません。**

### 5. 検証と PR

合成データで、新ラベル、未知ラベルの拒否、ファイル欄、文字コード往復、エラー保持、同フレームのモーフと
ボーンの保護をテストします。`python -m unittest discover -s tests -v` で全体を実行します。
`python scripts/smoke_mcp.py` は MCP と schema、オフライン処理を確認し、既定ではウィンドウを読み取り専用で列挙します。
保存済みテスト工程では `smoke_current_mme.py --apply --hwnd $MmdHwnd` を必要に応じて使います。
事前にコードを読み、割当の再入力と任意のモデル選択が行われることを理解してください。
`smoke_scene.py`、`smoke_release.py`、`smoke_editing.py` はテスト用 MMD を起動・編集します。
必要な範囲のみ検証し、未実施の機能を対応済みと記載しません。

自動テスト、実機で確認した範囲、未検証の範囲を区別して記録します。
公開前にファイル、差分、PR 本文、コミット情報を調べ、端末固有のパス、ユーザー名、私用メール、秘密情報、
実際の素材名、画像、実行記録を除きます。合成相対パスを使い、生成物は無視対象ディレクトリに保持します。
必要に応じて GitHub の非公開メールを使用します。独立互換ブランチを宛先にする場合、
存在と作成権限を確認して PR の base を明示し、`main` への誤送信を避けます。

## English

This workflow helps maintainers and agents adapt mmd-mcp to their own MMD distribution.
See the [compatibility guide](zh-ja-patched-mme.md) for the existing mixed-UI profile.
Validate UI, file encoding, controllers, and native bone operations as separate capabilities.

### 1. Establish a baseline and protect the project

Create a dedicated branch from a known upstream commit. Record that commit, Windows/Python bitness,
MMD/MME versions, and patch provenance. Save a project copy first. Use an existing or dedicated test instance,
read tool schemas before calling them, and acquire fresh window handles.
To identify a user-supplied executable, run `Get-FileHash -LiteralPath $MmdExe -Algorithm SHA256` locally.
A digest identifies a build; it neither proves layout compatibility nor justifies relaxing validation.

### 2. Inspect actual controls and labels

From the repository root, run `python scripts/call_mmd.py mmd_list_windows` and `list-tools`.
Read `mmd_get_ui_state` and `mmd_get_dialogs`, and check screenshots. If the current reader rejects the build,
use read-only Win32 enumeration scoped to the selected process to inspect titles, classes, IDs, text,
and parent relationships. Keep diagnostic dumps and screenshots local.

- `ui_language.py`: add exact observed aliases and verify the actual naming mode in `english_mode`.
  A translated UI does not establish the encoding of model or bone names.
- `ui_state.py`: compare control IDs and owning windows; add an explicit adapter and tests only for actual differences.
- `file_operations.py`: separately inspect OS open/save dialogs, filename edits, buttons, and overwrite confirmations.
- `scene_lifecycle.py`, `accessory_controls.py`, `edit_actions.py`: validate individual confirmation texts when those
  operations are needed. Keep unverified destructive operations rejected; do not substitute broad substrings or generic OK buttons.

### 3. Verify encoding and an EMM roundtrip

Read the active code page with `python -c "import ctypes; print(ctypes.windll.kernel32.GetACP())"`.
Export an EMM with synthetic Chinese test paths, decode strictly, and verify that the paths resolve to test files.
Do not infer encoding from UI language or suppress decoding errors.
An encoding extension must cover read/write in `effects.py`, live transfers in `effects_live.py`,
schemas in `server.py`, and regression tests. Offline operations default to CP932; this branch automatically
selects CP936 only for active code page 936. Existing files support explicit selection; other code pages require validation.

Export a baseline, read it with the same encoding, write identical assignments to a new copy, import, and re-export.
Compare object paths, exact render targets, Owner, material subsets, visibility, frame, selection, and scene settings.
EMM IDs are transient and are not UI model indices; compare object identities if numbering changes.

### 4. Separate controller UI from native bone access

Read actual morph names and trial a morph-only `mmd_batch_bone_keys` request at the current frame with
`register_key=false`. Verify readback and avoid unnecessary frame evaluation. This UI path can be adapted independently
of bone memory access.

If bone enumeration, selection, or transforms are required, separately verify encoding, layouts, pointers,
and strides in `bone_state.py`, plus call targets, calling conventions, and UI-thread behavior in
`native/selection_bridge.cpp`. Use disposable scenes and retain the original executable restriction until
the migration and regression testing are supported by evidence. **Changing the hash alone is not a native port.**

### 5. Test, document scope, and prepare the PR

Add synthetic regressions for aliases, unknown-label refusal, file controls, encoding roundtrips,
error propagation, same-frame morphs, and native bone guards. Run `python -m unittest discover -s tests -v`.
`python scripts/smoke_mcp.py` checks MCP initialization, schemas, and offline operations; by default it also lists windows read-only.
Optionally run `smoke_current_mme.py --apply --hwnd $MmdHwnd` on a saved test project after reading the script:
it reimports assignments and its optional morph check temporarily changes model selection.
`smoke_scene.py`, `smoke_release.py`, and `smoke_editing.py` launch and edit test instances.
Run only the needed scope and do not claim untested capabilities.

Document automated checks, actual live checks, and unverified operations separately.
Before publishing, inspect files, patches, PR text, and commit metadata. Remove machine-specific paths,
usernames, private email addresses, secrets, actual asset names, screenshots, and runtime reports.
Use synthetic relative paths; keep generated artifacts in ignored directories and use a GitHub privacy email if needed.
For a separate compatibility target, verify that the base branch exists and you can create it before explicitly
setting the PR base, avoiding an unintended target of `main`.
