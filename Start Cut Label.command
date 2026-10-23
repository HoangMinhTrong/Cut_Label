#!/bin/zsh
cd "${0:A:h}" || exit 1
sh ./launch.sh
result=$?
if [[ $result -ne 0 ]]; then
  read '?Khong khoi dong duoc. Kiem tra Internet va Release v1.0.0. Nhan Enter de dong.'
fi
exit $result
