from flask import (
    Blueprint,send_from_directory, flash, g,current_app, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from flaskr.auth import login_required
from flaskr.db import get_db
import markdown, uuid
from datetime import datetime
import os

bp = Blueprint('blog', __name__)


def generate_unique_filename(filename):
    extention = filename.rsplit('.',1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if extention:
        unique_filename = f"{unique_filename}.{extention}"
    return unique_filename



@bp.route('/')
def index():
    db = get_db()
    user_id = 0
    if g.user is not None:
        user_id = g.user['id']
    

    query = '''SELECT p.id, title, body, p.created, author_id, username, count(distinct l.id) as likes, count(DISTINCT c.id) as comments_count,
    CASE WHEN ul.post_id IS NOT NULL THEN 1 ELSE 0 END AS user_liked, GROUP_CONCAT(DISTINCT t.tag) AS tags 
    FROM post p 
    JOIN user u ON p.author_id = u.id 
    LEFT JOIN likes l on p.id = l.post_id 
    LEFT JOIN likes ul on ul.post_id = p.id AND ul.user_id = ? 
    LEFT JOIN comments c on c.post_id = p.id
    LEFT JOIN post_tag pt on pt.post_id = p.id
    LEFT JOIN tags t on pt.tag_id = t.id 
    GROUP BY p.id, p.title, p.body, p.created, p.author_id, u.username
    ORDER BY p.created DESC'''
    posts = db.execute(query, (user_id,)).fetchall()

    len_per_page = 15
    page = request.args.get('page', 1, type=int)
    start_page = (page-1)*len_per_page 
    end_page = start_page+len_per_page
    paginated_posts = posts[start_page:end_page]
    total_pages = (len(posts)+len_per_page-1)//len_per_page
    
    paginated_posts_dict = [dict(post) for post in paginated_posts]

    images_by_post = {}
    for post in paginated_posts:
        images = db.execute('SELECT * FROM images where post_id=?',(post['id'],)).fetchall()
        if images:
            images_by_post[post['id']]=images
        #print(images_by_post) #{58: [<sqlite3.Row object at 0x000001F3DD43AEF0>, <sqlite3.Row object at 0x000001F3DD43AF50>]}



    for content in paginated_posts_dict:
        content['body'] = markdown.markdown(content['body'])


    return render_template('blog/index.html', page=page,posts=paginated_posts_dict,total_pages=total_pages,images_by_post=images_by_post)

'''The purpose of this JOIN operation is to combine the data from the post table and the user table so that 
you can retrieve information about both the post and the user who created it in a single query.

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view'''


'''def create():
    # function body
create = login_required(create)
'''


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = request.form['tags']
        image_file = request.files['image']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor()

            cursor.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            post_id = cursor.lastrowid
            print(post_id)

            if tags:
                tag_names = [tag.strip() for tag in tags.split('#')]
                tag_ids = []
            
                for tag in tag_names:
                    tag_id_database = db.execute('SELECT id FROM tags where tag =?',(tag,)).fetchone()
                    if tag_id_database:
                       tag_id = tag_id_database[0]
                       tag_ids.append(tag_id)
                    else: 
                       db.execute('INSERT INTO tags(tag) VALUES(?)',(tag,))
                       db.commit()
                       #tag_id = db.last_insert_rowid
                       tag_id=db.execute('SELECT id from tags WHERE tag=?', (tag,)).fetchone()[0]
                       tag_ids.append(tag_id)
                tag_ids = set(tag_ids)
                for tag_id in tag_ids:
                    db.execute('INSERT INTO post_tag(post_id,tag_id) VALUES(?,?)',(post_id,tag_id))
                    db.commit()

            if image_file and image_file.filename:
                filename = secure_filename(generate_unique_filename(image_file.filename))
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'],filename) # app object created inside create_app() is local to that function scope. It is returned from the factory function and typically stored in a variable in your main application script (e.g., app = create_app() in run.py). Once the Flask application (app) is created, it is accessible via the current_app context variable within the request context.
                image_file.save(file_path)

                db.execute('INSERT INTO images(post_id,filename) VALUES(?,?)',(post_id, filename))
                db.commit()

            
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


'''Both the update and delete views will need to fetch a post by id and check if the author matches the 
logged in user. To avoid duplicating code, you can write a function to get the post and call it from each view.'''


'''404 means “Not Found”, and 403 means “Forbidden”. 
(401 means “Unauthorized”, but you redirect to the login page instead of returning that status.)

WHERE clause in a query, it is applied after the FROM clause and any JOIN operations, but before the GROUP BY,
 HAVING, and ORDER BY clauses. I'''

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p'
        ' JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post



@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

'''The pattern {{ request.form['title'] or post['title'] }} is used to choose what data appears in the form. 
When the form hasn’t been submitted, the original post data appears, but if invalid form data was posted you want to display that so the user can fix the error, so request.form is used instead. request is another variable that’s automatically available in templates.'''



@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


'''The delete view doesn’t have its own template, the delete button is part of update.html and posts to the /<id>/delete URL. Since there is no template, 
it will only handle the POST method and then redirect to the index view.'''


#A detail view to show a single post. Click a post’s title to go to its page.
@bp.route('/<int:id>', methods=('GET',))
def post(id):
    db = get_db()
    user_id = 0
    if g.user is not None:
        user_id = g.user['id']

    query = '''SELECT p.id, title, body, p.created, author_id, username, count(DISTINCT l.id) as likes, count(DISTINCT c.id) as comment_count,
    CASE WHEN ul.post_id IS NOT NULL THEN 1 ELSE 0 END AS user_liked 
    FROM post p 
    JOIN user u ON p.author_id = u.id 
    LEFT JOIN likes l on p.id = l.post_id 
    LEFT JOIN likes ul on ul.post_id = p.id AND ul.user_id = ?
    LEFT JOIN comments c on p.id = c.post_id
    WHERE p.id=? 
    GROUP BY p.id, p.title, p.body, p.created, p.author_id, u.username
    ORDER BY p.created DESC'''
    post = db.execute(query, (user_id, id)).fetchone()

    comments = db.execute(('SELECT c.id, c.comment,c.post_id,c.user_id, u.username, c.created'
                          ' FROM comments c'
                          ' LEFT JOIN user u on u.id = c.user_id'  
                          ' WHERE c.post_id =?'
                          ' ORDER BY c.created DESC'),(id,)).fetchall()
    
    images_by_post = db.execute('SELECT * FROM images where post_id=?',(id,)).fetchall()
    #print(images_by_post) #[<sqlite3.Row object at 0x000002DDFCBE1FF0>]

    

    error = None
    if not post:
        error = 'No Post Found'
        return redirect(url_for('blog.index'))
    

    return render_template('blog/post.html',post=post, comments=comments,images_by_post=images_by_post)


#a view for like
@bp.route('/<int:id>/like', methods=('POST',))
@login_required
def likeMeOrNot(id):
    if request.method == 'POST':
        page = request.args.get('page')
        db = get_db()
        count = db.execute("SELECT count(*) FROM likes WHERE post_id=? and user_id=?",(id, g.user['id'])).fetchone()[0]
        if(count == 0 ):
            db.execute(
                'INSERT INTO likes(post_id, user_id) VALUES(?,?)',(id,g.user['id'])
                )
        else: db.execute('DELETE FROM likes where post_id=? and user_id=?',(id,g.user['id']))
        db.commit()
    
    index_page = request.args.get('post_page')
    if index_page == 'true':
        return redirect(url_for('blog.post',id=id))
    
    
    return redirect(url_for('blog.index',page=page))

#a view for comments
@bp.route('/<int:id>/comment',methods=('POST',))
@login_required
def comment(id):
    if request.method == 'POST':
        page = request.args.get('page')
        db = get_db()
        error = None
        comment = request.form['comment']
        user_id = g.user['id']      
        if comment: 
            db.execute("INSERT INTO comments(comment, post_id,user_id) Values(?,?,?)",(comment, id, user_id))
        else:
            error = 'comment is empty'  
        db.commit()

    return redirect(url_for('blog.post',id=id,page=page))


@bp.route('/<int:post_id>/delete/<int:comment_id>/', methods=('POST',))
@login_required
def delete_comment(post_id, comment_id):
    db = get_db()
    db.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    db.commit()
    return redirect(url_for('blog.post', id=post_id))


@bp.route('/tag/<string:tag_name>', methods=('GET',))
def tags(tag_name):
    user_id = 0
    db =get_db()
    if g.user is not None:
        user_id = g.user['id']
    posts = db.execute('''SELECT p.id, p.title, p.body, p.created, p.author_id, u.username, COUNT(DISTINCT l.id) as likes, 
                       GROUP_CONCAT(DISTINCT t.tag) as tags, CASE WHEN ul.post_id IS NOT NULL THEN 1 ELSE 0 END AS user_liked 
                       from post p 
                       LEFT JOIN post_tag pt ON p.id = pt.post_id  
                       LEFT JOIN tags t ON t.id=pt.tag_id 
                       LEFT JOIN post_tag pt_specific ON pt_specific.post_id = p.id AND pt_specific.tag_id IN (SELECT id FROM tags where tag=?) 
                       LEFT JOIN user u on u.id=p.author_id 
                       LEFT JOIN likes l on l.post_id= p.id 
                       LEFT JOIN likes ul on ul.post_id = p.id AND ul.user_id = ?
                       WHERE pt_specific.tag_id IS NOT NULL 
                       GROUP BY p.id
                       ORDER BY p.created DESC''',
                       (tag_name,user_id)
                       ).fetchall()
    return render_template('blog/tag.html',posts=posts)


@bp.route('/search>',methods=('GET','POST'))
def search():

    if request.method == 'GET':
        query = request.args.get('query')   
    
        db =get_db()
        users = db.execute('SELECT username FROM user WHERE username=?',(query,)).fetchone()
        posts = db.execute(''' SELECT p.id, p.title, p.title, p.created,p.body, u.username 
                       FROM post p
                       JOIN user u ON p.author_id = u.id
                       WHERE body LIKE ? OR BODY LIKE ?;''', ('%'+ query + '%','%' + query + '%')).fetchall()
        
    
    return render_template('blog/search.html',posts=posts,users=users,query=query)

    

    
    
@bp.app_errorhandler(404)
def global_page_not_found(e):
    return render_template('blog/404.html'),404


@bp.route('/uploads/<filename>')
def uploaded_in_instance(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],filename)
    
