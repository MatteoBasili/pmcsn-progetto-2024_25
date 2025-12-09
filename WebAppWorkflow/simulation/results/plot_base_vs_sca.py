import os
import numpy as np
import matplotlib.pyplot as plt

from src.utils import INFINITE_FOLDER

SCENARIO_BASE = "light_1FA"
SCENARIO_SCA  = "light_2FA"


# ============================================================
#   FUNZIONI DI SUPPORTO
# ============================================================

def autolabel_bars(a, b, fmt="{:.6f}"):
    for bar in b:
        height = bar.get_height()
        a.annotate(fmt.format(height),
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 4),  # offset verticale
                   textcoords="offset points",
                   ha="center", va="bottom",
                   fontsize=10, fontweight="bold")

def mean(data):
    a = np.array(data)
    m = np.mean(a)

    return m

def load_metric_values(metric, scenario):
    filename = f"{metric}_{scenario}.dat"
    path = os.path.join(INFINITE_FOLDER, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"File non trovato: {filename}")

    with open(path, "r") as f:
        values = [float(line.strip()) for line in f.readlines()]

    return values


# ============================================================
#   1) CONFRONTO RT + TEST 20%
# ============================================================

rt_1fa_vals = load_metric_values("RT", SCENARIO_BASE)
rt_2fa_vals = load_metric_values("RT", SCENARIO_SCA)

rt_1fa_mean = mean(rt_1fa_vals)
rt_2fa_mean = mean(rt_2fa_vals)

delta_rt = (rt_2fa_mean - rt_1fa_mean) / rt_1fa_mean * 100

print("\n================  CONFRONTO RT  =================")
print(f"RT medio {SCENARIO_BASE}: {rt_1fa_mean:.6f} s")
print(f"RT medio {SCENARIO_SCA} : {rt_2fa_mean:.6f} s")
print(f"Incremento percentuale: {delta_rt:.6f} %")

if delta_rt > 20:
    print("⚠️  SUPERATA SOGLIA DEL 20%")
else:
    print("✅  SOTTO LA SOGLIA DEL 20%")
print("=================================================\n")


fig1, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(["1FA", "2FA"], [rt_1fa_mean, rt_2fa_mean])
ax.set_ylabel("RT medio [s]")
ax.set_title("Confronto Tempo di Risposta (RT)")
ax.grid(True, alpha=0.3)

autolabel_bars(ax, bars, fmt="{:.6f}")

plt.tight_layout()
plt.show()


# ============================================================
#   2) CONFRONTO RICHIESTE IN ESECUZIONE
# ============================================================

n_1fa_vals = load_metric_values("N_system", SCENARIO_BASE)
n_2fa_vals = load_metric_values("N_system", SCENARIO_SCA)

n_1fa_mean = mean(n_1fa_vals)
n_2fa_mean = mean(n_2fa_vals)

fig2, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(["1FA", "2FA"], [n_1fa_mean, n_2fa_mean])
ax.set_ylabel("Numero medio di richieste in esecuzione")
ax.set_title("Confronto Numero di Richieste")
ax.grid(True, alpha=0.3)

autolabel_bars(ax, bars, fmt="{:.6f}")

plt.tight_layout()
plt.show()


# ============================================================
#   3) CONFRONTO THROUGHPUT
# ============================================================

th_1fa_vals = load_metric_values("Throughput", SCENARIO_BASE)
th_2fa_vals = load_metric_values("Throughput", SCENARIO_SCA)

th_1fa_mean = mean(th_1fa_vals)
th_2fa_mean = mean(th_2fa_vals)

fig3, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(["1FA", "2FA"], [th_1fa_mean, th_2fa_mean])
ax.set_ylabel("Throughput [req/s]")
ax.set_title("Confronto Throughput")
ax.grid(True, alpha=0.3)

autolabel_bars(ax, bars, fmt="{:.6f}")

plt.tight_layout()
plt.show()


# ============================================================
#   4) CONFRONTO UTILIZZAZIONI
# ============================================================

servers = ["A", "B", "P"]

u_1fa_vals = {s: load_metric_values(f"U_{s}", SCENARIO_BASE) for s in servers}
u_2fa_vals = {s: load_metric_values(f"U_{s}", SCENARIO_SCA) for s in servers}

u_1fa_mean = [mean(u_1fa_vals[s]) for s in servers]
u_2fa_mean = [mean(u_2fa_vals[s]) for s in servers]

x = np.arange(len(servers))
w = 0.35

fig4, ax = plt.subplots(figsize=(7, 4))
bars1 = ax.bar(x - w/2, u_1fa_mean, w, label="1FA")
bars2 = ax.bar(x + w/2, u_2fa_mean, w, label="2FA")

ax.set_xticks(x)
ax.set_xticklabels(servers)
ax.set_ylabel("Utilizzazione U")
ax.set_title("Confronto Utilizzazioni per Server")
ax.legend()
ax.grid(True, alpha=0.3)

autolabel_bars(ax, bars1, fmt="{:.6f}")
autolabel_bars(ax, bars2, fmt="{:.6f}")

plt.tight_layout()
plt.show()


# ============================================================
#   5) CONFRONTO SERVICE DEMANDS (VALIDAZIONE SCA)
# ============================================================

d_1fa_vals = {s: load_metric_values(f"D_{s}", SCENARIO_BASE) for s in servers}
d_2fa_vals = {s: load_metric_values(f"D_{s}", SCENARIO_SCA) for s in servers}

d_1fa_mean = [mean(d_1fa_vals[s]) for s in servers]
d_2fa_mean = [mean(d_2fa_vals[s]) for s in servers]

fig5, ax = plt.subplots(figsize=(7, 4))
bars1 = ax.bar(x - w/2, d_1fa_mean, w, label="1FA")
bars2 = ax.bar(x + w/2, d_2fa_mean, w, label="2FA")

ax.set_xticks(x)
ax.set_xticklabels(servers)
ax.set_ylabel("Service Demand D")
ax.set_title("Confronto Service Demands per Server")
ax.legend()
ax.grid(True, alpha=0.3)

autolabel_bars(ax, bars1, fmt="{:.6f}")
autolabel_bars(ax, bars2, fmt="{:.6f}")

plt.tight_layout()
plt.show()
