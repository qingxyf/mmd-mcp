"""Synthetic regression cases for Chinese-patched UI and CP936 EMM files."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import win32gui

from mmd_mcp import bone_batch as bb
from mmd_mcp import effects, effects_live
from mmd_mcp import file_operations as files
from mmd_mcp.ui_language import english_mode, matches, variants


class ChineseUICompatibilityTests(unittest.TestCase):
    def test_mixed_chinese_mode_buttons(self):
        for label, source in (("相機編", "カメラ編"), ("模型編", "モデル編")):
            with self.subTest(label=label):
                self.assertTrue(matches(label, source))
                reader = Mock()
                reader.text.return_value = label
                self.assertFalse(english_mode(reader))

    def test_chinese_windows_save_dialog_has_exact_filename_control(self):
        dialog = {"title": "另存为", "controls": [
            {"hwnd": 10, "class": "Edit", "id": 1001},
            {"hwnd": 11, "class": "Edit", "id": 41477},
        ]}
        parents = {10: 20, 20: 30, 11: 40}
        classes = {20: "ComboBox", 30: "FloatNotifySink", 40: "Address Band Root"}
        with patch.object(files.win32gui, "GetParent", side_effect=parents.get), \
             patch.object(files.win32gui, "GetClassName", side_effect=classes.get):
            self.assertEqual(files.filename_edit(dialog), 10)
        self.assertIn("另存为", variants(files.SAVE_DIALOG_TITLES))

    def test_chinese_windows_open_dialog_ignores_the_address_bar(self):
        dialog = {"title": "打开", "controls": [
            {"hwnd": 10, "class": "Edit", "id": 1148},
            {"hwnd": 11, "class": "Edit", "id": 41477},
        ]}
        with patch.object(files.win32gui, "GetParent", return_value=20), \
             patch.object(files.win32gui, "GetClassName", return_value="ComboBox"):
            self.assertEqual(files.filename_edit(dialog), 10)
        self.assertIn("打开", variants(files.FILE_DIALOG_TITLES))

    def test_unknown_translations_are_rejected(self):
        reader = Mock()
        reader.text.return_value = "未知编辑模式"
        with self.assertRaisesRegex(ValueError, "Unsupported MMD UI language"):
            english_mode(reader)
        self.assertIsNone(files.filename_edit({"title": "允许覆盖所有文件", "controls": []}))
        self.assertFalse(matches("相機編 - 确认删除", "カメラ編"))

    def test_shell_can_destroy_filename_control_during_completion(self):
        dialog = {"title": "另存为", "controls": [
            {"hwnd": 10, "class": "Edit", "id": 1001},
        ]}
        error = win32gui.error(1400, "GetParent", "Invalid window handle")
        with patch.object(files.win32gui, "GetParent", side_effect=error), \
             patch.object(files.win32gui, "IsWindow", return_value=False):
            self.assertIsNone(files.filename_edit(dialog))

    def test_live_filename_control_errors_are_not_suppressed(self):
        dialog = {"title": "另存为", "controls": [
            {"hwnd": 10, "class": "Edit", "id": 1001},
        ]}
        error = win32gui.error(1400, "GetParent", "Invalid window handle")
        with patch.object(files.win32gui, "GetParent", side_effect=error), \
             patch.object(files.win32gui, "IsWindow", return_value=True):
            with self.assertRaises(win32gui.error):
                files.filename_edit(dialog)

    def test_unrelated_window_errors_are_not_suppressed(self):
        dialog = {"title": "打开", "controls": [
            {"hwnd": 10, "class": "Edit", "id": 1148},
        ]}
        error = win32gui.error(5, "GetParent", "Access denied")
        with patch.object(files.win32gui, "GetParent", side_effect=error), \
             patch.object(files.win32gui, "IsWindow", return_value=False):
            with self.assertRaises(win32gui.error):
                files.filename_edit(dialog)


class ChineseEffectsCompatibilityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "before.emm"

    def test_cp936_emm_preserves_chinese_paths_and_unedited_bytes(self):
        destination = self.directory / "after.emm"
        original = (
            "; 中文路径编码验证\r\n[Info]\r\nVersion = 3\r\n"
            "[Object]\r\nPmd1 = 模型/示例模型.pmx\r\nAcs2 = effects/ray.x\r\n"
            "[Effect]\r\nDefault = none\r\nPmd1 = none\r\n"
            "[Effect@MaterialMap]\r\nOwner = Acs2\r\n"
            "; 保留材质可见性\r\nPmd1[2] = none\r\nPmd1[2].show = false\r\n"
        ).encode("cp936")
        self.source.write_bytes(original)
        data = effects.read_emm(str(self.source), encoding="cp936")
        self.assertEqual(data["objects"]["Pmd1"], "模型/示例模型.pmx")
        self.assertEqual(data["encoding"], "cp936")
        result = effects.write_emm(
            str(self.source), {"Pmd1": "渲染预设/主渲染.fx"},
            output_path=str(destination), encoding="cp936")
        self.assertEqual(result["encoding"], "cp936")
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(destination.read_bytes(), original.replace(
            b"Pmd1 = none", "Pmd1 = 渲染预设/主渲染.fx".encode("cp936")))
        after = effects.read_emm(str(destination), encoding="cp936")
        self.assertEqual(after["effects"]["Pmd1"], "渲染预设/主渲染.fx")
        self.assertEqual(after["effect_sections"]["Effect@MaterialMap"],
                         data["effect_sections"]["Effect@MaterialMap"])

    def test_live_import_decodes_explicit_encoding_before_ui_action(self):
        self.source.write_bytes(
            "[Object]\r\nPmd1 = 模型.pmx\r\n[Effect]\r\nPmd1 = none\r\n".encode("cp936"))
        with patch.object(effects_live, "UIReader", side_effect=RuntimeError("stop before UI")), \
             patch.object(effects_live.ctypes.windll.kernel32, "GetACP") as get_acp:
            with self.assertRaisesRegex(RuntimeError, "stop before UI"):
                effects_live.transfer("import", str(self.source), encoding="cp936")
        get_acp.assert_not_called()

    def test_live_import_selects_cp936_or_preserves_japanese_default(self):
        self.source.write_bytes(b"[Object]\r\nPmd1 = model.pmx\r\n[Effect]\r\nPmd1 = none\r\n")
        for code_page, expected in ((936, "cp936"), (932, "cp932")):
            with self.subTest(code_page=code_page), \
                 patch.object(effects_live.ctypes.windll.kernel32, "GetACP", return_value=code_page), \
                 patch.object(effects_live.effects, "read_emm", wraps=effects.read_emm) as read, \
                 patch.object(effects_live, "UIReader", side_effect=RuntimeError("stop before UI")):
                with self.assertRaisesRegex(RuntimeError, "stop before UI"):
                    effects_live.transfer("import", str(self.source))
                read.assert_called_once_with(str(self.source), encoding=expected)

    def test_unknown_emm_encoding_is_rejected(self):
        self.source.write_bytes(b"[Info]\r\nVersion = 3\r\n")
        with self.assertRaisesRegex(ValueError, "encoding"):
            effects.read_emm(str(self.source), encoding="utf-7")


class MorphOnlyCompatibilityTests(unittest.TestCase):
    def test_controller_adjustment_avoids_bone_memory_and_same_frame_seek(self):
        reader = Mock()
        reader.text.return_value = "相機編"
        reader.combo.return_value = {"items": ["Exposure+"], "selected_index": 0}
        keyed = {"morph": "other:Exposure+", "weight": 0.25, "registered": False}
        with patch.object(bb, "UIReader", return_value=reader), \
             patch.object(bb.scene, "context", return_value=("0", 1, "controller")), \
             patch.object(bb, "BoneMemory", side_effect=ValueError("unsupported executable")) as memory, \
             patch.object(bb.scene, "commit_number") as commit, \
             patch.object(bb, "_key_morph", return_value=keyed) as key:
            result = bb.batch_bone_keys([bb.FrameItem(frame=0, register_key=False,
                morphs=[{"category": "other", "name": "Exposure+", "weight": 0.25}])], hwnd=1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["bone_keys"], 0)
        self.assertEqual(result["frames_completed"][0]["morphs"], [keyed])
        memory.assert_not_called()
        commit.assert_not_called()
        key.assert_called_once()

    def test_morph_only_batch_seeks_when_target_frame_differs(self):
        reader = Mock()
        reader.text.return_value = "相機編"
        reader.combo.return_value = {"items": ["Exposure+"], "selected_index": 0}
        frame = [0]

        def context(_reader, _mode):
            return str(frame[0]), 1, "controller"

        def seek(_reader, control_id, value):
            self.assertEqual(control_id, 417)
            frame[0] = value

        with patch.object(bb, "UIReader", return_value=reader), \
             patch.object(bb.scene, "context", side_effect=context), \
             patch.object(bb, "BoneMemory", side_effect=ValueError("unsupported executable")) as memory, \
             patch.object(bb.scene, "commit_number", side_effect=seek) as commit, \
             patch.object(bb, "_key_morph", return_value={"registered": True}):
            result = bb.batch_bone_keys([bb.FrameItem(frame=10,
                morphs=[{"category": "other", "name": "Exposure+", "weight": 0.25}])],
                return_to_frame=False, hwnd=1)
        self.assertEqual(result["displayed_frame"], 10)
        commit.assert_called_once_with(reader, 417, 10)
        memory.assert_not_called()

    def test_bone_batch_still_requires_verified_native_layout(self):
        reader = Mock()
        reader.text.return_value = "相機編"
        with patch.object(bb, "UIReader", return_value=reader), \
             patch.object(bb.scene, "context", return_value=("0", 1, "model")), \
             patch.object(bb, "BoneMemory", side_effect=ValueError("unsupported executable")) as memory, \
             patch.object(bb.scene, "commit_number") as commit:
            with self.assertRaisesRegex(ValueError, "unsupported executable"):
                bb.batch_bone_keys([bb.FrameItem(frame=0,
                    bones=[{"name": "頭", "rotation_degrees": {"x": 5.0}}])], hwnd=1)
        memory.assert_called_once()
        commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
