hello:
  # test rule
	echo "Hello world!"

create:
  # make directories for certain concentrations
  # in config.json, we defined type 1 to be Fe and type 2 to be Cr
  # so, we start at 86% Fe, and end at 99%, stepping at 1%
  # similarly for Cr, 1% to 14% with step 1%
  # this will create directories with template files and fill out those template files according to the config file
	python src/make_dirs.py \
		--start 0.86 0.01 \
		--step 0.01 0.01 \
		--end 0.99 0.14 \

submit: create
  # change into directories matching concentration pattern and run the submission job
  # submission.sh submits MD runs for 1000 K to 1300 K with step 50 K
  # TODO put those temperatures in this rule
	for dir in [0-9]*_[0-9]*/; \
		do \
		cd $$dir; \
		./submission.sh; \
		cd ..; \
	done

clean:
  # remove directories created above
	rm -rf [0-9]*_[0-9]*/

compress:
  # compress resulting dump files in parallel
  # IMPORTANT: do not run this while simulations are still running, wait for them to finish
	find . -name "*.dump" -type f -exec pigz {} +