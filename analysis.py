from pathlib import Path

import ovito
import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import matplotlib as mpl


def total_displacement_modifier(frame: int, data: ovito.data.DataCollection) -> None:
    
    types = data.particles['Particle Type'][...]
    per_particle_displacements = data.particles['Displacement'][...]

    # get per-type data and reduce it
    for type_ in set(types):
        displacements_of_type = per_particle_displacements[types == type_]
        data.attributes[f'Total displacement {type_:.0f}'] = np.sum(displacements_of_type, axis=0)


def ensemble_average(time_series: NDArray) -> tuple[NDArray, NDArray, NDArray]:

    if len(time_series.shape) == 1:
        average, num_samples = ensemble_average(time_series[:, np.newaxis])
        return average.squeeze(), num_samples.squeeze()

    average = np.zeros_like(time_series)
    num_samples = np.zeros_like(time_series, dtype=int)

    for j in range(len(time_series)):

        sliding_views = np.lib.stride_tricks.sliding_window_view(
            time_series,
            (j, 1)
        )[:, 0, :, :]
        if j > 0:
            changes = sliding_views[:, -1, :] - sliding_views[:, 0, :]
        elif j == 0:
            changes = np.zeros((sliding_views.shape[0], sliding_views.shape[2]))
        num_samples[j], _ = changes.shape
        average[j, :] = np.mean(changes, axis=0)

    return average, num_samples


def main():

    dump_file_path = Path("93_7/dump_files/transport_1250_I.dump.gz")
    pipeline = ovito.io.import_file(dump_file_path)

    pipeline.modifiers.append(ovito.modifiers.CalculateDisplacementsModifier())
    pipeline.modifiers.append(total_displacement_modifier)

    data = pipeline.compute(0)
    unique_types = set(data.particles['Particle Type'][...])
    total_displacement_all = np.zeros((len(unique_types), pipeline.source.num_frames, 3))
    timestep = np.zeros(pipeline.source.num_frames)
    
    for frame in range(pipeline.source.num_frames):

        data = pipeline.compute(frame)
        timestep[frame] = data.attributes["Timestep"]
        for t in unique_types:
            total_displacement_all[t - 1, frame, :] = data.attributes[f"Total displacement {t:.0f}"]

    fig, axs = plt.subplots(nrows=2, sharex=True)

    for t1 in unique_types:
        for t2 in unique_types:
            if t1 > t2:
                continue
            total_displacement_t1, total_displacement_t2 = total_displacement_all[t1 - 1, :, :], total_displacement_all[t2 - 1, :, :]
            dot_product = np.einsum("ti,ti->t", total_displacement_t1, total_displacement_t2)
            # smooth out by ensemble averaging
            dot_product, num_samples = ensemble_average(dot_product)
            axs[0].plot(timestep, dot_product, label=f"{t1:.0f}{t2:.0f}")
            if t1 == t2:
                axs[1].plot(timestep, num_samples, color="black")

    axs[0].set_ylabel(r"$\left\langle \mathbf{R}_\alpha(t)\cdot \mathbf{R}_\beta(t)\right\rangle$")
    axs[0].grid()
    axs[0].legend(title=r"$\alpha\beta$")

    axs[1].set_ylabel("sample size")
    axs[1].set_xlabel(r"$t$ (timesteps)")
    axs[1].grid()

    fig.tight_layout()
    fig.savefig("msd.pdf")


if __name__ == "__main__":

    mpl.use("Agg")
    main()
