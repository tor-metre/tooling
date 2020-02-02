
import googleapiclient.discovery 



if __name__ == '__main__':
    name = 'test-image'
    zone = 'us-central1-a'
    location = 'tor-with-timer'
    stateFile = 'gs://hungry-serpent//1.state'
    create_instance(zone,name,location,stateFile)