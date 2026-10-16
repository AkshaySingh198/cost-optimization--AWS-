# Useful Commands
python -c "from src.detection.eip import check_eip; print(check_eip())"
python -c "import sys; sys.path.insert(0, 'src'); from lamda import lambda_handler; print(lambda_handler({}, None))"
terraform -chdir=terraform apply