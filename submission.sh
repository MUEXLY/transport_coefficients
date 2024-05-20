for d in V I; do
    for ((t=1000; t<=1300; t+=50)); do
        python pbs_file.py --temperature ${t} --defect ${d} | qsub
    done
done