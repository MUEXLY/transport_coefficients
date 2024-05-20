hello:
	echo "Hello world!"

create:
	python make_dirs.py \
		--start 0.9 0.1 \
		--step 0.05 0.05 \
		--end 0.95 0.15 \

submit: create
	for dir in [0-9]*_[0-9]*/; \
		do \
		cd $$dir; \
		./submission.sh; \
		cd ..; \
	done

clean:
	rm -rf [0-9]*_[0-9]*/