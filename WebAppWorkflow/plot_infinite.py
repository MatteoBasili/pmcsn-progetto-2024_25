import os
import matplotlib.pyplot as plt

# cartella con i .dat
folder = "results/infinite/"

# statistiche da plottare
stats = [
    "mean_rt",
    "throughput_rps",
    "A_util",
    "B_util",
    "P_util",
    "A_avg_n",
    "B_avg_n",
    "P_avg_n"
]

for stat in stats:
    file_path = os.path.join(folder, f"{stat}.dat")
    if not os.path.isfile(file_path):
        print(f"Attenzione: file non trovato: {file_path}")
        continue

    # legge i valori
    with open(file_path, "r") as f:
        ys = [float(line.strip()) for line in f if line.strip()]

    xs = list(range(len(ys)))  # batch index

    # crea il grafico
    plt.figure(figsize=(10, 4))
    plt.plot(xs, ys, marker='o', linestyle='-', label=stat)
    plt.xlabel("Batch index")
    plt.ylabel(stat)
    plt.title(f"{stat} vs batch")
    plt.grid(True)
    plt.legend()

    # salva il grafico
    out_png = os.path.join(folder, f"{stat}.png")
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"Grafico salvato in {out_png}")
