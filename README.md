# transport_coefficients

There are a couple of things you need to edit.

## Configuration

First, in `config.json`:

```json
{
    "executable": "./lmp",
    "potential": {
        "pair_style": "meam",
        "pair_coeff": "* * library.meam Co Ni Cr Fe Mn CoNiCrFeMn.meam Fe Cr",
        "files": ["CoNiCrFeMn.meam", "library.meam"]
    },
    "borrowing_index": 0,
    "epsilon": 1e-10
}
```

Be sure to change the name of the executable to match your executable. You can probably just change `./lmp` to `lmp`, I just don't put LAMMPS into my bin.

Changing the subdictionary in `potential` here is crucial. `pair_style` and `pair_coeff` are the commands defined in the LAMMPS documentation [here](https://docs.lammps.org/pair_style.html) and [here](https://docs.lammps.org/pair_coeff.html), and `files` is a list of any files necessary to include to fully define those commands. For many pair styles, this list will have no members or just one member. In any case, be sure that this is indeed a list.

`borrowing_index` defines whatever the "host" element is. In my case, for FeCr, the host element is Fe. You can choose whatever host element provided that host element is present in all of your samples.

`epsilon` defines a small number necessary for some comparisons. It's unlikely you need to change this.

## Makefile

Next, in `Makefile`, change the parameters run in the `create` rule. These are described inside of `Makefile`.

To create directories for your compositions and submit jobs for them, run:

```sh
make submit
```

Once the jobs are finished, you can run the following to compress the (likely large) dump files:

```sh
make compress
```

This will compress all of the dump files in formats that are readable, without decompression, by both OVITO and NumPy.