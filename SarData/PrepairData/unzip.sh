#!/bin/bash
# Check if zip file is unzipped or not. If not unzipped yet, unzip it
    for zipfile in *.zip; do
      echo $zipfile
      zipfileName=${zipfile%%.zip}
      if [[ ! -d "${zipfileName}.SAFE" ]]; then
        unzip -q $zipfile
      else
        echo "Zip file has been already unzipped"
      fi
    done
mkdir archivedData
mv *.zip ./archivedData/


