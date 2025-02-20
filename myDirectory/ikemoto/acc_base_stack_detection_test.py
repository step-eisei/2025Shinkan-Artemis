import matplotlib.pyplot as plt
import csv
import math


# File path
file_path = "../../record/test/fall_val_test_20250204-163512.csv"

# Lists to store time and acc_x, acc_y, acc_z data
time_data = []
acc_x_data = []
acc_y_data = []
acc_z_data = []

# Read the CSV file
with open(file_path, "r") as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # Skip the header
    for row in csvreader:
        time_data.append(float(row[0]))  # time[s]
        acc_x_data.append(float(row[2]))  # acc_x[g]
        acc_y_data.append(float(row[3]))  # acc_y[g]
        acc_z_data.append(float(row[4]))  # acc_z[g]

stack_time_data = []
stack_acc_x_data = []
stack_acc_y_data = []
stack_acc_z_data = []


for t, acc_x, acc_y, acc_z in zip(time_data, acc_x_data, acc_y_data, acc_z_data):
    if 25 <= t <= 40:
        # if 0 <= t <= 15:
        stack_time_data.append(t)
        stack_acc_x_data.append(acc_x)
        stack_acc_y_data.append(acc_y)
        stack_acc_z_data.append(acc_z)


# Plotting the modified acc_x graph
plt.figure(figsize=(10, 6))
plt.plot(
    stack_time_data,
    stack_acc_x_data,
    label="acc_x[g]",
    color="r",
)
plt.show()

# Plotting the modified acc_y graph
plt.figure(figsize=(10, 6))
plt.plot(
    stack_time_data,
    stack_acc_y_data,
    label="acc_x[g]",
    color="r",
)
plt.show()

# Plotting the modified acc_z graph
plt.figure(figsize=(10, 6))
plt.plot(
    stack_time_data,
    stack_acc_z_data,
    label="acc_x[g]",
    color="r",
)
plt.show()


stack_acc_diff = (
    170 * (10 ** (-6)) * math.sqrt(100) * 5
)  # ADXL367: Low noise to 170 µg/√Hz, low_g_acc3_output_rate = 100 Hz
# stack_acc_diff = 0.04
last_acc_x = stack_acc_x_data[0]
last_acc_y = stack_acc_y_data[1]
last_acc_z = stack_acc_z_data[2]
stack_count = 0
not_stack_count = 0

for i in range(1, len(stack_acc_x_data)):
    if (
        math.fabs(stack_acc_x_data[i] - last_acc_x) <= stack_acc_diff
        and math.fabs(stack_acc_y_data[i] - last_acc_y) <= stack_acc_diff
        and math.fabs(stack_acc_z_data[i] - last_acc_z) <= stack_acc_diff
    ):
        stack_count += 1
    else:
        not_stack_count += 1
    last_acc_x = stack_acc_x_data[i]
    last_acc_y = stack_acc_y_data[i]
    last_acc_z = stack_acc_z_data[i]

print(f"{stack_count=}")
print(f"{not_stack_count=}")
