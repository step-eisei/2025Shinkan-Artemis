import matplotlib.pyplot as plt
import csv

# File path
file_path = "../../record/test/fall_val_test_20250204-163512.csv"

# Lists to store time and acc_norm data
time_data = []
acc_norm_data = []

# Read the CSV file
with open(file_path, "r") as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # Skip the header
    for row in csvreader:
        time_data.append(float(row[0]))  # time[s]
        acc_norm_data.append(float(row[5]))  # acc_norm[g]


# Plotting the modified acc_norm graph
plt.figure(figsize=(10, 6))
plt.plot(
    time_data,
    acc_norm_data,
    label="acc_norm[g]",
    color="r",
)
plt.xlabel("Time [s]")
plt.ylabel("Acceleration Norm [g]")
plt.legend()
plt.grid(True)
plt.show()

# Cut out data between 0s to 25s and reverse time
calib_time_data = []
calib_acc_norm_data = []

for t, acc in zip(time_data, acc_norm_data):
    if 25 <= t <= 40:
        calib_time_data.append(t)
        calib_acc_norm_data.append(acc)

# Plotting the modified acc_norm graph
plt.figure(figsize=(10, 6))
plt.plot(
    calib_time_data,
    calib_acc_norm_data,
    label="acc_norm[g]",
    color="r",
)

mean_calib_acc_norm = (
    sum(calib_acc_norm_data) / len(calib_acc_norm_data) if calib_acc_norm_data else 0
)
print(f"Mean of calib_acc_norm_data: {mean_calib_acc_norm}")


plt.xlabel("Time [s]")
plt.ylabel("Acceleration Norm [g]")
plt.legend()
plt.grid(True)
plt.show()

# Cut out data between 0s to 25s and reverse time
cut_time_data = []
cut_acc_norm_data = []

for t, acc in zip(time_data, acc_norm_data):
    if 15 <= t <= 20:
        cut_time_data.append(t)
        cut_acc_norm_data.append(acc)

# Plotting the modified acc_norm graph
plt.figure(figsize=(10, 6))
plt.plot(
    cut_time_data,
    cut_acc_norm_data,
    label="acc_norm[g] (0s to 25s, reversed time)",
    color="r",
)
plt.xlabel("Time [s]")
plt.ylabel("Acceleration Norm [g]")
plt.title("Acceleration Norm over Time (0s to 25s)")
plt.legend()
plt.grid(True)
plt.show()

# Modify acc_norm data
# modified_acc_norm_data = [1 - acc for acc in cut_acc_norm_data]
modified_acc_norm_data = [mean_calib_acc_norm - acc for acc in cut_acc_norm_data]


# Plotting the modified acc_norm graph
plt.figure(figsize=(10, 6))
plt.plot(
    cut_time_data,
    modified_acc_norm_data,
    label="Modified acc_norm[g] (1 - acc_norm)",
    color="b",
)
plt.xlabel("Time [s]")
plt.ylabel("Modified Acceleration Norm [g]")
plt.title("Modified Acceleration Norm over Time (0s to 25s)")
plt.legend()
plt.grid(True)
plt.show()

velocity = 0
velocitys = []
t_before = 0
acc_before = 0
count = 0
for t, acc in zip(cut_time_data, modified_acc_norm_data):
    if count == 1:
        t_before = t
        acc_before = acc
        continue

    # 台形積分による数値積分
    velocity += (acc + acc_before) * (t - t_before) / 2 * 9.8
    velocitys.append(velocity)
    t_before = t
    acc_before = acc

# Plotting velocity graph
plt.figure(figsize=(10, 6))
plt.plot(
    cut_time_data,
    velocitys,
    label="velocity[m/s^2]",
    color="b",
)
plt.xlabel("Time [s]")
plt.ylabel("Velocity [m/s^2]")
plt.title("Integral modified acc")
plt.legend()
plt.grid(True)
plt.ylim(-4, 6)  # Show y grid until 6 m/s^2
plt.show()
