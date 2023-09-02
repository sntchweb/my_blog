from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Likes, Post, User
from posts.utils import get_pages


@cache_page(10, key_prefix='index_page')
def index(request):
    """Главная страница."""

    return render(
        request,
        'posts/index.html',
        {
            'page_obj': get_pages(
                request,
                Post.objects.select_related('author', 'group').all()),
            'last_post': Post.objects.latest('pub_date')
        }
    )


def group_posts(request, slug):
    """Страница сообщества."""

    return render(
        request,
        'posts/group_list.html',
        {
            'page_obj': get_pages(
                request,
                get_object_or_404(
                    Group.objects.prefetch_related('posts'),
                    slug=slug).posts.all()
            ),
            'group': get_object_or_404(Group, slug=slug),
        }
    )


def profile(request, username):
    """Страница профиля."""

    author = get_object_or_404(
        User.objects.prefetch_related('posts__group'), username=username
    )
    if (request.user.is_authenticated) and (request.user != author) and not (
            Follow.objects.filter(user=request.user, author=author).exists()):
        return render(
            request,
            'posts/profile.html',
            {
                'author': author,
                'page_obj': get_pages(request, author.posts.all()),
            }
        )
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': get_pages(request, author.posts.all()),
            'following': True,
        }
    )


def post_detail(request, post_id):
    """Страница записи."""

    post = get_object_or_404(Post.objects.annotate(
        posts_count=Count('author__posts', distinct=True),
        comments_count=Count('comments', distinct=True)
    ).prefetch_related(Prefetch(
        'comments',
        queryset=Comment.objects.select_related('author'))), pk=post_id)
    if (request.user.is_authenticated) and not (
        Likes.objects.filter(
            user=request.user,
            post=get_object_or_404(Post, pk=post_id)).exists()):
        return render(
            request,
            'posts/post_detail.html',
            {
                'post': post,
                'form': CommentForm(request.POST or None),
            }
        )
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'form': CommentForm(request.POST or None),
            'liked': True
        }
    )


@login_required
def post_create(request):
    """Страница создания записи."""

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    """Страница редактирования записи."""

    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if not form.is_valid():
        context = {'form': form, 'is_edit': True}
        return render(request, 'posts/create_post.html', context)
    post = form.save()
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""

    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return redirect('posts:post_detail', post_id=post_id)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница подписок."""

    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': get_pages(
                request,
                Post.objects.filter(author__following__user=request.user))
        }
    )


@login_required
def profile_follow(request, username):
    """Подписаться на автора записи."""

    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора записи."""

    get_object_or_404(
        Follow,
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).delete()
    return redirect('posts:profile', username=username)


@login_required
def post_delete(request, post_id):
    """Удаление записи."""

    post = get_object_or_404(Post, pk=post_id)
    if request.user == post.author:
        get_object_or_404(Post, pk=post_id).delete()
    return redirect('posts:profile', username=request.user.username)


@login_required
def post_like(request, post_id):
    """Поставить лайк на запись."""

    Likes.objects.get_or_create(
        user=request.user,
        post=get_object_or_404(Post, pk=post_id)
    )
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_unlike(request, post_id):
    """Убрать лайк с записи."""

    get_object_or_404(
        Likes,
        user=request.user,
        post=get_object_or_404(Post, pk=post_id)
    ).delete()
    return redirect('posts:post_detail', post_id=post_id)
