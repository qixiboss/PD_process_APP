import pandas as pd
import numpy as np
import re
from scipy.signal import find_peaks

# --- 配置和常量 ---

JOINT_NAMES = {
    0: "PELVIS", 1: "SPINE_NAVAL", 2: "SPINE_CHEST", 3: "NECK", 4: "CLAVICLE_LEFT",
    5: "SHOULDER_LEFT", 6: "ELBOW_LEFT", 7: "WRIST_LEFT", 8: "HAND_LEFT", 9: "HANDTIP_LEFT",
    10: "THUMB_LEFT", 11: "CLAVICLE_RIGHT", 12: "SHOULDER_RIGHT", 13: "ELBOW_RIGHT",
    14: "WRIST_RIGHT", 15: "HAND_RIGHT", 16: "HANDTIP_RIGHT", 17: "THUMB_RIGHT",
    18: "HIP_LEFT", 19: "KNEE_LEFT", 20: "ANKLE_LEFT", 21: "FOOT_LEFT", 22: "HIP_RIGHT",
    23: "KNEE_RIGHT", 24: "ANKLE_RIGHT", 25: "FOOT_RIGHT", 26: "HEAD", 27: "NOSE",
    28: "EYE_LEFT", 29: "EAR_LEFT", 30: "EYE_RIGHT", 31: "EAR_RIGHT"
}
JOINT_IDS = {name: i for i, name in JOINT_NAMES.items()}
FPS = 30.0


# --- 核心分析类 ---

class GaitAnalyzer:
    def __init__(self, data_filepath, fps=FPS):
        self.fps = fps
        print(f"正在从 '{data_filepath}' 加载数据...")
        self.data = self._load_skeleton_data(data_filepath)
        if self.data is None or self.data.empty:
            print("数据加载失败，程序退出。")
            exit()

        self.frames = sorted(self.data['frame'].unique())
        self.results = {}
        self.scores = {}
        print(f"数据加载完成，共 {len(self.frames)} 帧。")

    def _load_skeleton_data(self, filepath):
        data_records = []
        current_frame_id = None
        frame_regex = re.compile(r"Frame: (\d+)")
        joint_regex = re.compile(r"Joint (\d+): ([\d\.-]+), ([\d\.-]+), ([\d\.-]+)")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    frame_match = frame_regex.search(line)
                    if frame_match:
                        current_frame_id = int(frame_match.group(1))
                        continue
                    joint_match = joint_regex.search(line)
                    if joint_match and current_frame_id is not None:
                        joint_id = int(joint_match.group(1))
                        pos_x = float(joint_match.group(2))
                        pos_y = float(joint_match.group(3))
                        pos_z = float(joint_match.group(4))
                        data_records.append(
                            {'frame': current_frame_id, 'joint_id': joint_id, 'pos_x': pos_x, 'pos_y': pos_y,
                             'pos_z': pos_z})

            if not data_records:
                print("错误：文件中未找到有效的骨骼数据。")
                return None
            df = pd.DataFrame(data_records)
            if df[['pos_x', 'pos_y', 'pos_z']].abs().mean().mean() > 100:
                print("坐标值似乎是毫米，将自动转换为米。")
                df[['pos_x', 'pos_y', 'pos_z']] /= 1000.0

            self.structured_data = {}
            for frame_id, group in df.groupby('frame'):
                self.structured_data[frame_id] = {row.joint_id: np.array([row.pos_x, row.pos_y, row.pos_z]) for _, row
                                                  in group.iterrows()}
            return df
        except FileNotFoundError:
            print(f"错误：找不到文件 {filepath}")
            return None
        except Exception as e:
            print(f"读取或解析文件时出错: {e}")
            return None

    def _get_joint_pos(self, frame, joint_name):
        joint_id = JOINT_IDS[joint_name]
        return self.structured_data.get(frame, {}).get(joint_id)

    # --- 修复点 1：修改此函数以返回真实的帧号 ---
    def _detect_steps(self):
        left_ankle_z, right_ankle_z, pelvis_z = [], [], []
        valid_frames_for_steps = []

        for frame in self.frames:
            la_pos = self._get_joint_pos(frame, "ANKLE_LEFT")
            ra_pos = self._get_joint_pos(frame, "ANKLE_RIGHT")
            p_pos = self._get_joint_pos(frame, "PELVIS")

            if all(pos is not None for pos in [la_pos, ra_pos, p_pos]):
                left_ankle_z.append(la_pos[2])
                right_ankle_z.append(ra_pos[2])
                pelvis_z.append(p_pos[2])
                valid_frames_for_steps.append(frame)  # 记录下有效的帧号

        if not left_ankle_z or not right_ankle_z:
            print("错误：无法获取足够的脚踝或骨盆数据来检测步态。")
            return np.array([]), np.array([])

        left_z_rel = np.array(left_ankle_z) - np.array(pelvis_z)
        right_z_rel = np.array(right_ankle_z) - np.array(pelvis_z)

        left_peak_indices, _ = find_peaks(left_z_rel, distance=self.fps * 0.4, prominence=0.05)
        right_peak_indices, _ = find_peaks(right_z_rel, distance=self.fps * 0.4, prominence=0.05)

        # 将峰值索引映射回真实的帧号
        left_strike_frames = [valid_frames_for_steps[i] for i in left_peak_indices]
        right_strike_frames = [valid_frames_for_steps[i] for i in right_peak_indices]

        return left_strike_frames, right_strike_frames

    def analyze(self):
        print("开始步态分析...")
        self.left_strikes, self.right_strikes = self._detect_steps()

        if len(self.left_strikes) < 2 or len(self.right_strikes) < 2:
            print("警告：检测到的有效步数不足（少于2步），结果可能非常不准确。")
            self._calculate_gait_speed()
            self._calculate_arm_swing()
            self._calculate_trunk_flexion()
            self.results.update({'avg_step_length': 0, 'step_length_cv': 0, 'step_length_asymmetry': 0})
        else:
            print(f"检测到 {len(self.left_strikes)} 次左脚着地, {len(self.right_strikes)} 次右脚着地。")
            self._calculate_gait_speed()
            self._calculate_step_params()
            self._calculate_arm_swing()
            self._calculate_trunk_flexion()

        print("分析完成。")

    def _calculate_gait_speed(self):
        start_pos = self._get_joint_pos(self.frames[0], "PELVIS")
        end_pos = self._get_joint_pos(self.frames[-1], "PELVIS")
        if start_pos is None or end_pos is None:
            self.results['gait_speed'] = 0
            return
        distance = np.linalg.norm(end_pos[[0, 2]] - start_pos[[0, 2]])
        duration = (self.frames[-1] - self.frames[0]) / self.fps
        self.results['gait_speed'] = distance / duration if duration > 0 else 0

    # --- 修复点 2：修复此函数中的崩溃和逻辑 ---
    def _calculate_step_params(self):
        left_steps_len, right_steps_len = [], []

        # 使用纯Python列表操作，避免Numpy歧义
        left_events = [(frame, 'L') for frame in self.left_strikes]
        right_events = [(frame, 'R') for frame in self.right_strikes]
        all_strikes = sorted(left_events + right_events)

        step_lengths = []
        for i in range(1, len(all_strikes)):
            frame1, side1 = all_strikes[i - 1]
            frame2, side2 = all_strikes[i]

            if side1 != side2:  # 确保是交替步
                ankle1_name = "ANKLE_LEFT" if side1 == 'L' else "ANKLE_RIGHT"
                ankle2_name = "ANKLE_LEFT" if side2 == 'L' else "ANKLE_RIGHT"

                pos1 = self._get_joint_pos(frame1, ankle1_name)
                pos2 = self._get_joint_pos(frame2, ankle2_name)

                if pos1 is not None and pos2 is not None:
                    length = np.linalg.norm(pos2[[0, 2]] - pos1[[0, 2]])
                    step_lengths.append(length)
                    if side2 == 'L':
                        left_steps_len.append(length)
                    else:
                        right_steps_len.append(length)

        self.results['avg_step_length'] = np.mean(step_lengths) if step_lengths else 0
        self.results['step_length_cv'] = np.std(step_lengths) / self.results['avg_step_length'] if self.results[
                                                                                                       'avg_step_length'] > 0 else 0

        mean_left = np.mean(left_steps_len) if left_steps_len else 0
        mean_right = np.mean(right_steps_len) if right_steps_len else 0
        if mean_left + mean_right > 0:
            self.results['step_length_asymmetry'] = abs(mean_left - mean_right) / ((mean_left + mean_right) / 2)
        else:
            self.results['step_length_asymmetry'] = 0

    def _calculate_arm_swing(self):
        left_swing, right_swing = [], []
        for frame_id in self.frames:
            lw_pos = self._get_joint_pos(frame_id, "WRIST_LEFT")
            ls_pos = self._get_joint_pos(frame_id, "SHOULDER_LEFT")
            rw_pos = self._get_joint_pos(frame_id, "WRIST_RIGHT")
            rs_pos = self._get_joint_pos(frame_id, "SHOULDER_RIGHT")

            if all(p is not None for p in [lw_pos, ls_pos, rw_pos, rs_pos]):
                left_swing.append(lw_pos[2] - ls_pos[2])
                right_swing.append(rw_pos[2] - rs_pos[2])

        self.results['left_arm_swing_range'] = np.ptp(left_swing) if left_swing else 0
        self.results['right_arm_swing_range'] = np.ptp(right_swing) if right_swing else 0
        avg_swing = (self.results['left_arm_swing_range'] + self.results['right_arm_swing_range']) / 2

        if avg_swing > 0.01:
            self.results['arm_swing_asymmetry'] = abs(
                self.results['left_arm_swing_range'] - self.results['right_arm_swing_range']) / avg_swing
        else:
            self.results['arm_swing_asymmetry'] = 0

    def _calculate_trunk_flexion(self):
        head_y_coords = [self._get_joint_pos(f, "HEAD")[1] for f in self.frames if
                         self._get_joint_pos(f, "HEAD") is not None]
        pelvis_y_coords = [self._get_joint_pos(f, "PELVIS")[1] for f in self.frames if
                           self._get_joint_pos(f, "PELVIS") is not None]

        if not head_y_coords or not pelvis_y_coords:
            self.results['avg_trunk_flexion'] = 0
            return

        y_up_direction = -1 if np.mean(head_y_coords) < np.mean(pelvis_y_coords) else 1
        vertical_vector = np.array([0, y_up_direction, 0])

        angles = []
        for frame in self.frames:
            pelvis = self._get_joint_pos(frame, "PELVIS")
            spine_chest = self._get_joint_pos(frame, "SPINE_CHEST")
            if pelvis is not None and spine_chest is not None:
                trunk_vector = spine_chest - pelvis
                if np.linalg.norm(trunk_vector) == 0: continue
                cosine_angle = np.dot(trunk_vector, vertical_vector) / (
                            np.linalg.norm(trunk_vector) * np.linalg.norm(vertical_vector))
                angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
                angles.append(np.degrees(angle))

        self.results['avg_trunk_flexion'] = np.mean(angles) if angles else 0

    def _score_feature(self, value, healthy_range, lower_is_better):
        h_min, h_max = healthy_range
        if lower_is_better:
            if value <= h_max: return 10.0
            score = 10.0 * (1 - (value - h_max) / (h_max * 2))
        else:
            if value >= h_min: return 10.0
            score = 10.0 * (value / h_min)
        return np.clip(score, 0, 10)

    def generate_report(self):
        if not self.results:
            print("没有分析结果可供报告。请先运行 .analyze()")
            return

        scoring_criteria = {
            'gait_speed': ([1.2, 1.4], False, 2.0),
            'avg_step_length': ([0.6, 0.8], False, 1.5),
            'avg_arm_swing': ([0.2, 0.5], False, 2.5),
            'arm_swing_asymmetry': ([0, 0.2], True, 2.0),
            'step_length_cv': ([0, 0.05], True, 1.0),
            'step_length_asymmetry': ([0, 0.1], True, 1.0),
            'avg_trunk_flexion': ([0, 15], True, 0.5),
        }

        self.results['avg_arm_swing'] = (self.results.get('left_arm_swing_range', 0) + self.results.get(
            'right_arm_swing_range', 0)) / 2

        total_score, total_weight = 0, 0

        print("\n" + "=" * 55)
        print("---           帕金森步态风险评估报告           ---")
        print("=" * 55)
        print(f"{'特征':<25} {'计算值':<15} {'评分 (0-10)':<15}")
        print("-" * 55)

        for feature, (healthy_range, lower_is_better, weight) in scoring_criteria.items():
            value = self.results.get(feature)
            if value is not None:
                score = self._score_feature(value, healthy_range, lower_is_better)
                self.scores[feature] = score
                total_score += score * weight
                total_weight += weight
                unit = 'm/s' if 'speed' in feature else 'deg' if 'flexion' in feature else 'm' if 'length' in feature or 'swing' in feature else ''
                value_str = f"{value:.3f} {unit}"
                print(f"{feature:<25} {value_str:<15} {f'{score:.1f}':<15}")

        final_score = (total_score / total_weight) * 10 if total_weight > 0 else 0

        print("-" * 55)
        print(f"加权总分: {final_score:.1f} / 100.0")
        print("=" * 55)

        print("\n--- 解读 ---")
        if final_score >= 80:
            print("步态特征整体在健康范围内，未见明显帕金森样体征。")
        elif 60 <= final_score < 80:
            print("步态存在轻微异常，部分指标（如步速或手臂摆动）偏离正常范围，建议关注。")
        elif 40 <= final_score < 60:
            print("步态表现出数个与帕金森病相关的特征，风险中等，建议进行专业评估。")
        else:
            print("步态表现出显著的帕金森样特征，风险较高。强烈建议咨询神经科医生进行全面诊断。")

        print("\n**重要免责声明：本结果仅为技术分析，不能替代专业医疗诊断。**")


# --- 主程序 ---
if __name__ == "__main__":
    # !!! 请将 "output25.3.15.txt" 替换成你的真实文件名 !!!
    data_file = "output25.3.15.txt"

    analyzer = GaitAnalyzer(data_filepath=data_file, fps=FPS)
    analyzer.analyze()
    analyzer.generate_report()
