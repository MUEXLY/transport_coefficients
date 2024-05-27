from pathlib import Path
from itertools import product

import ovito
import numpy as np
from numpy.typing import NDArray
from scipy.stats import linregress
import matplotlib.pyplot as plt
import matplotlib as mpl
import sqlalchemy as sql


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

    cr_fractions = range(1, 14 + 1, 1)
    temperatures = range(1000, 1300 + 50, 50)
    defects = ("V", "I")

    engine = sql.create_engine("sqlite:///transport.db")
    connection = engine.connect()
    metadata = sql.MetaData()

    table = sql.Table(
        "transport",
        metadata,
        sql.Column("id", sql.Integer, primary_key=True, autoincrement=True),
        sql.Column("temperature", sql.Integer),
        sql.Column("defect", sql.String),
        sql.Column("x_1", sql.Float),
        sql.Column("x_2", sql.Float),
        sql.Column("L_11", sql.Float),
        sql.Column("L_12", sql.Float),
        sql.Column("L_21", sql.Float),
        sql.Column("L_22", sql.Float)
    )

    metadata.create_all(engine)

    for cr_fraction, temperature, defect in product(cr_fractions, temperatures, defects):

        dump_file_path = Path(f"{100 - cr_fraction}_{cr_fraction}/dump_files/transport_{temperature}_{defect}.dump.gz")
        pipeline = ovito.io.import_file(dump_file_path)

        pipeline.modifiers.append(ovito.modifiers.CalculateDisplacementsModifier())
        pipeline.modifiers.append(total_displacement_modifier)

        data = pipeline.compute(0)
        unique_types = list(set(data.particles['Particle Type'][...]))
        total_displacement_all = np.zeros((len(unique_types), pipeline.source.num_frames, 3))
        time = np.zeros(pipeline.source.num_frames)
        
        for frame in range(pipeline.source.num_frames):

            data = pipeline.compute(frame)
            time[frame] = data.attributes["Timestep"] * 1.0e-6
            for t in unique_types:
                total_displacement_all[t - 1, frame, :] = data.attributes[f"Total displacement {t:.0f}"]

        fig, axs = plt.subplots(nrows=2, ncols=2, sharex=True)
        type_map = {1: r"\text{Fe}", 2: r"\text{Cr}"}
        onsager_matrix = np.zeros((2, 2))

        for i, t1 in enumerate(unique_types):
            for j, t2 in enumerate(unique_types):
                total_displacement_t1, total_displacement_t2 = total_displacement_all[t1 - 1, :, :], total_displacement_all[t2 - 1, :, :]
                dot_product = np.einsum("ti,ti->t", total_displacement_t1, total_displacement_t2) / 10
                # smooth out by ensemble averaging
                dot_product, num_samples = ensemble_average(dot_product)
                regression = linregress(time[num_samples >= 150], dot_product[num_samples >= 150])
                onsager_matrix[i, j] = regression.slope
                if t1 < t2:
                    continue
                axs[i, j].plot(time, dot_product, label="avg")
                axs[i, j].plot(time[num_samples >= 150], regression.intercept + regression.slope * time[num_samples >= 150], label=f"slope = {regression.slope:.2f} nm$^2$/ns")
                axs[i, j].set_ylabel(f"$\\left\\langle \\mathbf{{R}}_{{{type_map[t1]}}}(t)\\cdot \\mathbf{{R}}_{{{type_map[t2]}}}(t)\\right\\rangle$ (nm$^2$)")
                axs[i, j].grid()
                axs[i, j].legend()
            
        query = table.insert().values(
            temperature=temperature,
            defect=defect,
            x_1=100 - cr_fraction,
            x_2=cr_fraction,
            L_11=onsager_matrix[0, 0],
            L_12=onsager_matrix[0, 1],
            L_21=onsager_matrix[1, 0],
            L_22=onsager_matrix[1, 1]
        )
        connection.execute(query)
        connection.commit()

        axs[0, 1].plot(time, num_samples, color="black", linestyle="--")
        axs[0, 1].grid()
        axs[0, 1].set_ylabel("# of samples")

        full_defect_name = {
            "I": "self-interstitial",
            "V": "vacancy"
        }
        fig.suptitle(f"{cr_fraction:.0f}% Cr, {temperature} K, {full_defect_name[defect]}")
        fig.supxlabel("$t$ (ns)")
        fig.tight_layout()
        
        plot_path = Path(f"{100 - cr_fraction}_{cr_fraction}") / "plots"
        plot_path.mkdir(exist_ok=True)
        fig.savefig(plot_path / f"msd_plot_{temperature}_{defect}.pdf")
        plt.close(fig)


if __name__ == "__main__":

    mpl.use("Agg")
    main()
