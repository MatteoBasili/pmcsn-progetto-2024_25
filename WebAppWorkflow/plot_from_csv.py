import csv
import matplotlib.pyplot as plt

def load_mean_csv(filename):
    times = []
    means = []

    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row["time"]))
            means.append(float(row["mean_response_time"]))

    return times, means


def load_mean_ci_csv(filename):
    times = []
    means = []
    ci_low = []
    ci_up = []

    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row["time"]))
            means.append(float(row["mean"]))
            ci_low.append(float(row["ci_lower"]))
            ci_up.append(float(row["ci_upper"]))

    return times, means, ci_low, ci_up


def plot_mean(times, means, outfile="mean_curve.png"):
    plt.figure(figsize=(10,4))
    plt.plot(times, means, linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Mean Response Time (s)")
    plt.title("Mean Response Time Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outfile, dpi=200)
    print(f"[OK] Saved {outfile}")


def plot_mean_ci(times, means, ci_low, ci_up, outfile="mean_ci_curve.png"):
    plt.figure(figsize=(10,4))
    plt.plot(times, means, label="Mean", linewidth=2)
    plt.fill_between(times, ci_low, ci_up, alpha=0.3, label="95% CI")
    plt.xlabel("Time (s)")
    plt.ylabel("Response Time (s)")
    plt.title("Mean Response Time with 95% Confidence Interval")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(outfile, dpi=200)
    print(f"[OK] Saved {outfile}")


def load_matrix_csv(filename):
    data = []
    with open(filename) as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            data.append([float(x) for x in row])
    return header, data


def plot_all_replicas(header, matrix, outfile="all_replicas.png"):
    times = [float(t.replace("t=", "")) for t in header]

    plt.figure(figsize=(10,4))

    for row in matrix:
        plt.plot(times, row, color="gray", alpha=0.25)

    mean = [sum(matrix[r][i] for r in range(len(matrix))) / len(matrix)
            for i in range(len(matrix[0]))]

    plt.plot(times, mean, color="blue", linewidth=2, label="Mean")

    plt.xlabel("Time (s)")
    plt.ylabel("Response Time (s)")
    plt.title("All Replicas Response Times + Mean")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(outfile, dpi=200)
    print(f"[OK] Saved {outfile}")


if __name__ == "__main__":
    # Example usage:

    # 1. Plot mean only
    times, means = load_mean_csv("mean_response_time_300s.csv")
    plot_mean(times, means, "mean_curve.png")

    # 2. Plot mean ± CI
    #times, means, lo, up = load_mean_ci_csv("mean_ci_response_time_300s.csv")
    #plot_mean_ci(times, means, lo, up, "mean_ci_curve.png")

    # 3. Plot all 128 replicas
    header, matrix = load_matrix_csv("response_times_matrix_300s.csv")
    plot_all_replicas(header, matrix, "all_replicas.png")
