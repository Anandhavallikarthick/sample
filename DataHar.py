from googleapiclient.discovery import build
import pymongo
import pandas as pd
import streamlit as st


# Api key connection
def Api_connect():
    Api_Id="AIzaSyDfnrw51kqQQJqJ-6CzrRXBkZnk7ioyTa8"
    api_service_name="youtube"
    api_version="v3"
    youtube=build(api_service_name,api_version,developerKey=Api_Id)
    return youtube
youtube=Api_connect()



#1 get channel information by using the channel Id
def youtube_details(channel_id):
    request=youtube.channels().list(
    part="snippet,ContentDetails,statistics",
    id=channel_id
    )
    response=request.execute()
    for i in response['items']:
        data=dict(channel_Name=i["snippet"]["title"],
              channel_Id=i["id"],
              subscribers=i["statistics"]["subscriberCount"],
              views=i["statistics"]["viewCount"],
              Totalvideo=i["statistics"]["videoCount"],
              channel_Discription=i["snippet"]["description"],
              playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
    return data





# 2to get all video ids
def get_all_videoids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id,
                                    part='contentDetails').execute()
    Playlist_Id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token=None 

    while True:
        response1=youtube.playlistItems().list(
                                            part='snippet',
                                            playlistId=Playlist_Id,
                                            maxResults=50,
                                            pageToken=next_page_token).execute()
        
        for i in range(len(response1["items"])):
            video_ids.append(response1["items"][i]["snippet"]["resourceId"]["videoId"])
            next_page_token=response1.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids




# 3 get seperate information of individual videos(total)
def all_video_details(video_ids):
    video_data=[]
    for video_id in video_ids:
        request=youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response2=request.execute()
        
        
        for u in response2["items"]:
            data=dict(Channel_Name=u['snippet']['channelTitle'],
                      Channel_Id=u['snippet']['channelId'],
                      Video_Id=u['id'],
                      Title=u['snippet']['title'],
                      Tags=",".join(u['snippet'].get('tags',["NA"])),
                      Thumnails=u['snippet']['thumbnails']['default']['url'],
                      Description=u['snippet'].get('description'),
                      Published_Date=u['snippet']['publishedAt'],
                      Duration=u['contentDetails']['duration'],
                      Views=u['statistics'].get('viewCount'),
                      Comments=u['statistics'].get('commentCount'),
                      Favorite_count=u['statistics']['favoriteCount'],
                      Definition=u['contentDetails']['definition'],
                      Caption_status=u['contentDetails']['caption'],
                      likes=u['statistics'].get('likeCount')
            )
            video_data.append(data)
    return video_data



# 4 how to get the comment details.
def get_comment_details(video_ids):
    Comment_data=[]
    
    for video_id in video_ids:
        try:
            request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50

            )
            response3=request.execute()
            for item in response3['items']:
                data=dict(Comment_Id=item['snippet']['topLevelComment']['id'],
                        Video_id=item['snippet']['topLevelComment']['snippet']['videoId'],
                        Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        comment_Puplisheddate=item['snippet']['topLevelComment']['snippet']['publishedAt']
                        
                        )
                Comment_data.append(data)

        except:
            pass
    return Comment_data





#5 get playlist details
def get_playlist_details(channel_id):
        next_page_token=None
        playlist_data=[]
        while True:
                request=youtube.playlists().list(
                        part="snippet,contentDetails",
                        channelId=channel_id,
                        maxResults=50,
                        pageToken=next_page_token
                )
                response4=request.execute()

                for item  in response4['items']:
                        data=dict(Playlist_Id=item['id'],
                                Title=item['snippet']['title'],
                                Channel_Id=item['snippet']['channelId'],
                                Channel_Name=item['snippet']['channelTitle'],
                                PublishedAt=item['snippet']['publishedAt'],
                                Video_count=item['contentDetails']['itemCount']
                                )
                        playlist_data.append(data)
                next_page_token=response4.get('nextpageToken')
                if next_page_token is None:
                        break
        return playlist_data      




import pymongo
client=pymongo.MongoClient("mongodb+srv://anandhavallikarthick:Anandhi123@cluster0.p4dcodc.mongodb.net/?retryWrites=true&w=majority")
db=client["youtube_data"]
collection=db["channel_details1"]



def channel_details(channel_id):
    ch_details=youtube_details(channel_id)
    vid_id=get_all_videoids(channel_id)
    vid_details=all_video_details(vid_id)
    comment_details=get_comment_details(vid_id)
    playlist_details=get_playlist_details(channel_id)

    project=db["channel_details1"]
    project.insert_one({"channel_information":ch_details,"playlist_information":playlist_details,"video_information":vid_details,"comment_information":comment_details})
    
    return "upload completed successfully"




#1 full table sql
def channels_table():
  import mysql.connector
  mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
  )

  print(mydb)
  mycursor = mydb.cursor(buffered=True)
  mycursor.execute("use youtube_project")


  drop_query='''drop table if exists channels1'''
  mycursor.execute(drop_query)
  mydb.commit()

  create_query='''create table if not exists channels1(channel_Name varchar(100),channel_Id varchar(80) primary key,subscribers bigint,views bigint,Totalvideo int,channel_Discription text,playlist_Id varchar(80))'''
  mycursor.execute(create_query)
  mydb.commit()



  ch_list=[]
  db=client["youtube_data"]
  collection=db["channel_details1"]
  for ch_data in collection.find({},{"_id":0,"channel_information":1}):
      ch_list.append(ch_data["channel_information"])
  df=pd.DataFrame(ch_list)





  for index,row in df.iterrows():
      insert_query='''insert into channels1(channel_Name,channel_Id,subscribers,views,Totalvideo,channel_Discription,playlist_Id)values(%s,%s,%s,%s,%s,%s,%s)'''
      values=(row['channel_Name'],row['channel_Id'],row['subscribers'],row['views'],row['Totalvideo'],row['channel_Discription'],row['playlist_Id'])


    
      mycursor.execute(insert_query,values) 
      mydb.commit() 
     
      
# 2 nd full table
def videos_table():
  import mysql.connector
  mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
  )

  print(mydb)
  mycursor = mydb.cursor(buffered=True)
  mycursor.execute("use youtube_project")


  drop_query='''drop table if exists videos'''
  mycursor.execute(drop_query)
  mydb.commit()

  create_query='''create table if not exists videos(Channel_Name varchar(100),Channel_Id varchar(100),Video_Id varchar(50) primary key,Title varchar(150),Tags text,Thumnails varchar(200),Description text,Published_Date varchar(100),Duration varchar(50),Views bigint,Comments int,Favorite_count int,Definition varchar(40),Caption_status varchar(50),likes bigint)'''
  mycursor.execute(create_query)
  mydb.commit()




  vi_list=[]
  db=client["youtube_data"]
  collection=db["channel_details1"]
  for vi_data in collection.find({},{"_id":0,"video_information":1}):
      for i in range(len(vi_data["video_information"])):
          vi_list.append(vi_data["video_information"][i])
  df2=pd.DataFrame(vi_list)





  for index,row in df2.iterrows():
    insert_query='''insert into videos(Channel_Name,Channel_Id,Video_Id,Title,Tags,Thumnails,Description,Published_Date,Duration,Views,Comments,Favorite_count,Definition,Caption_status,likes)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    values=(row['Channel_Name'],row['Channel_Id'],row['Video_Id'],row['Title'],row['Tags'],row['Thumnails'],row['Description'],row['Published_Date'],row['Duration'],row['Views'],row['Comments'],row['Favorite_count'],row['Definition'],row['Caption_status'],row['likes'])
    mycursor.execute(insert_query,values)
    
    
  mydb.commit()













  







#3 full table
def playlist_table():
  import mysql.connector
  mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
  )

  print(mydb)
  mycursor = mydb.cursor(buffered=True)
  mycursor.execute("use youtube_project")



  drop_query='''drop table if exists playlists'''
  mycursor.execute(drop_query)
  mydb.commit()


  create_query='''create table if not exists playlists(Playlist_Id varchar(100) primary key,Title varchar(100),Channel_Id varchar(100),Channel_Name varchar(100),PublishedAt varchar(100),Video_count int)'''
  mycursor.execute(create_query)
  mydb.commit()


  play_list=[]
  db=client["youtube_data"]
  collection=db["channel_details1"]
  for play_data in collection.find({},{"_id":0,"playlist_information":1}):
      for i in range(len(play_data["playlist_information"])):
          play_list.append(play_data['playlist_information'][i])
  df3=pd.DataFrame(play_list)



  for index,row in df3.iterrows():
      insert_query='''insert into playlists(Playlist_Id,Title,Channel_Id,Channel_Name,PublishedAt,Video_count)values(%s,%s,%s,%s,%s,%s)'''
      values=(row['Playlist_Id'],row['Title'],row['Channel_Id'],row['Channel_Name'],row['PublishedAt'],row['Video_count'])
      mycursor.execute(insert_query,values)
      mydb.commit()
    



    
# 4 comment table
def comments_table():
    import mysql.connector
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
    )

    print(mydb)
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute("use youtube_project")



    drop_query='''drop table if exists comments'''
    mycursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists comments(Comment_Id varchar(100) primary key,Video_id varchar(100),Comment_Text text,Comment_Author varchar(150),comment_Puplisheddate varchar(100))'''
    mycursor.execute(create_query)
    mydb.commit()


    com_list=[]
    db=client["youtube_data"]
    collection=db["channel_details1"]
    for com_data in collection.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df4=pd.DataFrame(com_list)


    for index,row in df4.iterrows():
        insert_query='''insert into comments(Comment_Id,Video_id,Comment_Text,Comment_Author,comment_Puplisheddate)values(%s,%s,%s,%s,%s)'''
        values=(row['Comment_Id'],row['Video_id'],row['Comment_Text'],row['Comment_Author'],row['comment_Puplisheddate'])
        mycursor.execute(insert_query,values)
    mydb.commit()






def tables():
    channels_table()
    playlist_table()
    videos_table()
    comments_table()
    
    return "tables created sucessfully"

# data frame cration function.

def show_channels_table():
    ch_list=[]
    db=client["youtube_data"]
    collection=db["channel_details1"]
    for ch_data in collection.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list)
    return df


def show_videos_table():
  vi_list=[]
  db=client["youtube_data"]
  coll1=db["channel_details1"]
  for vi_data in coll1.find({},{"_id":0,"video_information":1}):
      for i in range(len(vi_data["video_information"])):
          vi_list.append(vi_data["video_information"][i])
  df2=st.dataframe(vi_list)
  return df2



def show_playlists_table():
    play_list=[]
    db=client["youtube_data"]
    collection=db["channel_details1"]
    for play_data in collection.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(play_data["playlist_information"])):
            play_list.append(play_data['playlist_information'][i])
    df3=st.dataframe(play_list)
    return df3



def show_comments_table():
    com_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details1"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df4=st.dataframe(com_list)
    return df4



# streamlit part

with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING USING MONGODB]")
    st.header("SKILL TAKE AWAY")
    st.caption("Python Scripting")
    st.caption("Data Collections")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption("Data Management using MongoDB and SQL")
channel_id=st.text_input("Enter the channel ID")


if st.button("collect and store data"):
  ch_ids=[]
  db=client["youtube_data"]
  collection=db["channel_details1"]
  for ch_data in collection.find({},{"_id":0,"channel_information":1}):
      ch_ids.append(ch_data["channel_information"]["Channel_Id"])
  if channel_id in ch_ids: 
     st.success("Channel Details of the given channel id already exists")
  else:
       insert=channel_details(channel_id)
       st.success(insert)
if st.button("Migrate to SQL"):
    Table=tables()
    st.success(Table) # to get the message in streamlit table created successfully


show_table=st.radio("SELECT THE TABLE FOR VIEW",("CHANNELS","PLAYLISTS","VIDEOS","COMMENTS"))


if show_table=="CHANNELS":
    show_channels_table()

if show_table=="PLAYLISTS":
    show_playlists_table()


if show_table=="VIDEOS":
    show_videos_table()


if show_table=="COMMENTS":
    show_comments_table()

     
         
  
    




# SQL connection for Query running in streamlit


import mysql.connector
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
)

print(mydb)
mycursor = mydb.cursor(buffered=True)
mycursor.execute("use youtube_project")

question=st.selectbox("SELECT YOUR QUESTIONS",("1. All the videos and the channel name",
                                               "2. Channels with most number of videos",
                                               "3. Top most 10 viewed videos",
                                               "4. Comments of each videos",
                                               "5. videos with highest likes",
                                               "6. Likes of all videos",
                                               "7. Views of each channels",
                                               "8. Videos Pulished in the year of 2022",
                                               "9. Videos with highest number of comments",
                                               "10. Average duration of all videos in each channels"))





if question=="1. All the videos and the channel name":
    query1='''select title as videos,channel_name as channelname from videos'''
    mycursor.execute(query1)
    mydb.commit()

    t1=mycursor.fetchall()
    df=pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)


elif question=="2. Channels with most number of videos":
    query2='''select channel_Name as channelname, Totalvideo as number_of_videos from channels1 order by Totalvideo desc'''
    mycursor.execute(query2)
    mydb.commit()

    t2=mycursor.fetchall()
    df2=pd.DataFrame(t2,columns=["channel name","number of videos"])
    st.write(df2)


elif question=="3. Top most 10 viewed videos":
    query3='''select views as views,channel_name as channelname,title as videotitle from videos where views is not null order by views desc limit 10'''
    mycursor.execute(query3)
    mydb.commit()

    t3=mycursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views","channel name","videotitle"])
    st.write(df3)



elif question=="4. Comments of each videos":
    query4='''select comments as no_comments,title as videotitle from videos where comments is not null'''
    mycursor.execute(query4)
    mydb.commit()

    t4=mycursor.fetchall()
    df4=pd.DataFrame(t4,columns=["no_comments","videotitle"])
    st.write(df4)


elif question=="5. videos with highest likes":
    query5='''select title as videotitle,channel_name as channelname,likes as likecount from videos where likes is not null order by likes desc'''
    mycursor.execute(query5)
    mydb.commit()

    t5=mycursor.fetchall()
    df5=pd.DataFrame(t5,columns=["videotitle","channelname","likecount"])
    st.write(df5)


elif question=="6. Likes of all videos":
    query6='''select likes as likecount,title as videotitle from videos'''
    mycursor.execute(query6)
    mydb.commit()

    t6=mycursor.fetchall()
    df6=pd.DataFrame(t6,columns=["likecount","videotitle"])
    st.write(df6)


elif question=="7. Views of each channels":
    query7='''select channel_name as channelname,views as totalviews from channels1'''
    mycursor.execute(query7)
    mydb.commit()

    t7=mycursor.fetchall()
    df7=pd.DataFrame(t7,columns=["channelname","totalviews"])
    st.write(df7)


elif question=="8. Videos Pulished in the year of 2022":
    query8='''select title as video_title,published_date as videorelease,channel_name as channelname from videos where extract(year from published_date)=2022'''
    mycursor.execute(query8)
    mydb.commit()

    t8=mycursor.fetchall()
    df8=pd.DataFrame(t8,columns=["video_title","videorelease","channelname"])
    st.write(df8)


elif question=="9. Videos with highest number of comments":
    query9='''select title as videotitle,channel_name as channelname,comments as comments from videos where comments is not null order by comments desc'''
    mycursor.execute(query9)
    mydb.commit()

    t9=mycursor.fetchall()
    df9=pd.DataFrame(t9,columns=["videotitle","channelname","comments"])
    st.write(df9)



elif question=="10. Average duration of all videos in each channels":
    query10='''select channel_name as channelname,AVG(duration) as averageduration from videos group by channel_name'''
    mycursor.execute(query10)
    mydb.commit()
    t10=mycursor.fetchall()
    df10=pd.DataFrame(t10,columns=["channelname","averageduration"])
    df10
    
    T10=[]
    for index,row in df10.iterrows():
        channel_title=row['channelname']
        average_duration==row['averageduration']
        average_duration_str=str(average_duration)
        T10.append(dict(channeltitle=channel_title,avgduration=average_duration_str))
    df0=pd.DataFrame(T10)
    st.write(df0)











