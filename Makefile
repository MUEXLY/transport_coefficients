hello:
	echo "Hello world!"

create:
	python src/make_dirs.py \
		--start 0.86 0.01 \
		--step 0.01 0.01 \
		--end 0.99 0.14 \

submit: create
	for dir in [0-9]*_[0-9]*/; \
		do \
		cd $$dir; \
		./submission.sh; \
		cd ..; \
	done

clean:
	rm -rf [0-9]*_[0-9]*/

compress:
	find . -name "*.dump" -type f -exec pigz {} +