from __future__ import annotations

import unittest

from heartbeat_yuanli_mcp.protocol import (
    CMD_APP_REQUEST,
    CMD_LINEAR,
    CMD_VIBRATION,
    DK_META2_PROFILE,
    MessageIdGenerator,
    build_action_frame,
    build_command_frame,
    calculate_checksum,
    get_device_profile,
    normalize_profile_name,
)


class ProtocolTests(unittest.TestCase):
    def test_checksum_is_twos_complement_of_payload_sum(self) -> None:
        self.assertEqual(calculate_checksum((CMD_VIBRATION, 50)), 0xC6)
        self.assertEqual(calculate_checksum((CMD_LINEAR, 0)), 0xF5)

    def test_command_frame_matches_official_layout(self) -> None:
        self.assertEqual(
            build_command_frame(1, CMD_VIBRATION, 50),
            bytes((0x01, CMD_APP_REQUEST, 0x00, 0x03, CMD_VIBRATION, 0x32, 0xC6)),
        )

    def test_message_ids_cycle_from_one_to_fifteen(self) -> None:
        ids = MessageIdGenerator()
        self.assertEqual([ids.next() for _ in range(17)], list(range(1, 16)) + [1, 2])

    def test_profile_and_tf_alias(self) -> None:
        self.assertEqual(normalize_profile_name("TF-META2\x00"), "DK-META2")
        self.assertEqual(get_device_profile("TF-META2"), DK_META2_PROFILE)
        self.assertEqual(get_device_profile("DK-META2").capabilities, ("vibration", "linear", "rotary"))

    def test_action_frame_rejects_unknown_action(self) -> None:
        with self.assertRaises(ValueError):
            build_action_frame(1, "heat", 1)

    def test_action_frame_rejects_out_of_range_level(self) -> None:
        with self.assertRaises(ValueError):
            build_action_frame(1, "vibration", 101)


if __name__ == "__main__":
    unittest.main()

