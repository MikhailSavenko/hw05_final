from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import MAX_POSTS

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from django.views.decorators.cache import cache_page


def paginator(posts, request):
    paginator = Paginator(posts, MAX_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return {
        "page_obj": page_obj,
    }


@cache_page(20, cache='default', key_prefix='index_page')
def index(request):
    title = "Последние обновления на сайте"
    posts = Post.objects.select_related()
    context = {
        "title": title,
    }
    context.update(paginator(posts, request))
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author")
    context = {
        "group": group,
        "title": f"Записи сообщества {group}",
    }
    context.update(paginator(posts, request))
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related("group")
    following = author.following.exists()
    context = {
        "author": author,
        "title": f"Профайл пользователя {author}",
        "posts": posts,
        "following": following,
    }
    context.update(paginator(posts, request))
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.count()
    form = CommentForm()
    comments = post.comments.all()
    context = {
        "post": post,
        "title": f"Пост: { post }",
        "posts_count": posts_count,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required(login_url="/auth/login/")
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect("posts:profile", request.user)
    return render(request, "posts/create_post.html", {"form": form})


@login_required(login_url="/auth/login/")
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    context = {
        "form": form,
        "post": post,
        "is_edit": True,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    context = {'title': "Лента подписок"}
    context.update(paginator(posts, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписаться"""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.filter(
            user=request.user,
            author=author
        ).delete()
    return redirect('posts:follow_index')
