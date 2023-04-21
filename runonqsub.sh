#!/bin/bash

folder="./"
script="./run_CLI_boost.sh"

for file in "$folder"/*; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        filename_no_ext="${filename%.*}"
        case "$filename" in
            *.mtz)
                qsub -P i23 -pe smp 5 -l gpu=4,gpu_arch=Volta "$script" "$filename_no_ext" "$filename" 
                ;;
            *)
                echo "Skipping $filename: not an MTZ file"
                ;;
        esac
    fi
done

        


