from CSDN import create_app

app = create_app()

print('')


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])