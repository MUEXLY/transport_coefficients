import sqlite3
from pathlib import Path
import re

import polars as pl
import matplotlib.pyplot as plt


def main():

    full_defect_name = {"I": "self-interstitial", "V": "vacancy"}
    column_name_pattern = re.compile(r'L_(\d{2})')
    type_map = {1: "Fe", 2: "Cr"}
    connection = sqlite3.connect("transport.db")

    for cr_fraction in range(1, 14 + 1, 1):

        fig, axs = plt.subplots(nrows=1, ncols=2, sharex=True, sharey=True)
        for ax, defect in zip(axs, ("V", "I")):
            df = pl.read_database(
                query="SELECT temperature, L_11, L_12, L_21, L_22 from transport WHERE x_2 = :x_2 and DEFECT = :defect",
                connection=connection,
                execute_options={"parameters": {"x_2": cr_fraction, "defect": defect}}
            )

            print(df)
        
            ax.grid()
            temperature = df["temperature"].to_list()
            for col in df.iter_columns():
                if not (match := column_name_pattern.match(col.name)):
                    continue
                # "12" -> "FeCr", etc
                pair = "".join(map(lambda x: type_map[int(x)], match.group(1)))
                ax.plot(temperature, col.to_list(), label=pair)

            ax.set_title(f"{full_defect_name[defect]}")

        axs[1].legend(title=r"$\alpha\beta$")
        axs[0].set_ylabel(r"$\ell_{\alpha\beta}$ (nm$^2$/ns)")
        fig.supxlabel("temperature (K)")
        fig.suptitle(f"{cr_fraction:.0f}% Cr")
        fig.savefig(Path(f"{100 - cr_fraction:.0f}_{cr_fraction:.0f}") / "coefficients.pdf")
        plt.close(fig)


if __name__ == "__main__":

    main()
